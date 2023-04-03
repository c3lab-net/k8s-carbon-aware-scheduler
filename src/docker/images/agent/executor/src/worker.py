#!/usr/bin/env -S python3 -u

import os
import yaml
import logging
import json
from shlex import quote
import traceback
from datetime import datetime, timezone, timedelta
import threading

from util import *
from postgres import *

class KubeHelper:
    """Helper tools with kubernetes."""

    @staticmethod
    def create_job(job_config):
        logging.info('Creating job using kubectl ...')
        try:
            job_yaml = yaml.dump(job_config)
            print(run_command('kubectl create -f -', job_yaml, print_command=True))
        except Exception as ex:
            raise ValueError(f'Failed to create job: {ex}') from ex


    @staticmethod
    def get_job_status_json(job_id):
        try:
            result = run_command(f'kubectl get job {quote(job_id)} ' +
                                    quote('-o=jsonpath={.status}'), print_command=False)
            return json.loads(result)
        except Exception as ex:
            raise ValueError(f'Failed to get job status json: {ex}') from ex

    @staticmethod
    def get_last_event_time_from_status_json(status_json, event_predicate = lambda _: True):
        try:
            l_conditions = status_json['conditions']
            filtered = filter(event_predicate, l_conditions)
            sorted = sorted(filtered, key=lambda e: e['lastTransitionTime'])
            return next(sorted, None)
        except Exception as ex:
            raise ValueError(f'Failed to get last event time from json status: {ex}') from ex


class JobLauncher:
    """Launch a job in kubernetes and record metadata."""

    def launch_job(self, request):
        job_id = request['job_id']
        job_config = self._create_job_config(request)
        self._save_job_config(job_id, job_config)
        KubeHelper.create_job(job_config)

    def _get_job_template(self):
        return load_yaml(os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'job.template.yaml'))

    def _create_job_config(self, request):
        logging.info('Creating job config ...')
        try:
            job_id = request['job_id']
            job_config = self._get_job_template()
            job_config['metadata']['name'] = job_id
            container = job_config['spec']['template']['spec']['containers'][0]
            container['name'] = f'{job_id}-container1'
            container['image'] = request['image']
            container['command'] = [ 'sh', '-c' ]
            container['args'] = [ '\n'.join(request['command']) ]
            container['resources']['requests']['cpu'] = get_dict_value_or_default(request, 'resources.requests.cpu', '1')
            container['resources']['requests']['memory'] = get_dict_value_or_default(request, 'resources.requests.memory', '256Mi')
            container['resources']['limits']['cpu'] = get_dict_value_or_default(request, 'resources.limits.cpu', '1')
            container['resources']['limits']['memory'] = get_dict_value_or_default(request, 'resources.requests.memory', '256Mi')
            volume_mounts = []
            for mount_path, storage in request['inputs'] | request['outputs']:
                [storage_type, paths] = storage
                match storage_type:
                    case 'pvc':
                        [pvc_name] = paths
                    case 's3':
                        raise NotImplementedError('s3 storage is not yet supported')
                    case _:
                        raise NotImplementedError(f'Unhandled storage type {storage_type}')
                volume_mounts.append({
                    'name': pvc_name,
                    'mountPath': mount_path,
                })
            container['volumeMounts'] = volume_mounts
            job_config['spec']['template']['spec']['containers'][0] = container
            return job_config
        except Exception as ex:
            raise ValueError(f'Failed to create job config: {ex}') from ex

    def _save_job_config(self, job_id, job_config):
        logging.info(f'Saving job config for {job_id}')
        try:
            conn = get_db_connection()
            with conn, conn.cursor() as cursor:
                result = psql_execute_list(cursor, 'INSERT INTO JobConfig (job_id, job_config) VALUES (%s, %s)', [
                    job_id, Json(job_config)
                ])
                logging.debug(result)
        except Exception as ex:
            raise ValueError(f'Failed to save job config (job_id={job_id}).') from ex


class JobTracker:
    """Track jobs that are pending and periodically update their status in database."""

    def __init__(self, update_frequency = timedelta(minutes=1)):
        self.tracked_job_ids = set()
        self.tracked_job_ids_lock = threading.Lock()
        self.update_daemon = threading.Timer(update_frequency.total_seconds(), self._update_all_job_status)

    def track_job(self, job_id):
        status = self._update_job_status(job_id)
        if status == 'Completed':
            return
        with self.tracked_job_ids_lock:
            self.tracked_job_ids.add(job_id)

    def save_job_history(self, job_id: str, event: str, timestamp: datetime):
        logging.info(f'Saving job history with job_id={job_id}, event={event}, timestamp={timestamp}')
        try:
            conn = get_db_connection()
            with conn, conn.cursor() as cursor:
                result = psql_execute_list(cursor, 'INSERT INTO JobHistory (job_id, event, time) VALUES (%s, %s, %s)', [
                    job_id, event, timestamp
                ])
                logging.debug(result)
        except Exception as ex:
            raise ValueError(f'Failed to save job history (job_id={job_id}).') from ex

    def _update_job_status(self, job_id):
        try:
            status_json = KubeHelper.get_job_status_json(job_id)
            return self._save_job_status_json(job_id, status_json)
        except Exception as ex:
            raise ValueError(f'Failed to update job status of {job_id}: {ex}') from ex

    def _update_all_job_status(self):
        tracked_job_ids = self.tracked_job_ids
        jobs_to_remove = set()
        for job_id in tracked_job_ids:
            try:
                status = self._update_job_status(job_id)
            except Exception as ex:
                logging.error(f'JobTracker update daemon: {ex}')
                logging.error(traceback.format_exc())
            if status == 'Completed':
                jobs_to_remove.add(job_id)

        if len(jobs_to_remove) > 0:
            return
        with self.tracked_job_ids_lock:
            for job_id in jobs_to_remove:
                self.tracked_job_ids.remove(job_id)

    def _save_job_status_json(self, job_id, status):
        logging.info(f'kubectl job status for {job_id}: {status}')
        try:
            if status.get('succeeded', 0) > 0 and 'completionTime' in status:
                event = 'Completed'
                timestamp = status['completionTime']
            elif status.get('failed', 0) > 0:
                event = 'Failed'
                timestamp = KubeHelper.get_last_event_time_from_status_json(status,
                                lambda e: e.get('status', None) is True and e.get('type', None) == 'Failed')
            elif 'startTime' in status:
                event = 'Started'
                timestamp = status['startTime']
            else:
                logging.error(f'Unhandled status for job {job_id}: {json.dumps(status)}')
                event = 'Unknown'
                timestamp = datetime.now(tz=timezone.utc)
            self.save_job_history(job_id, event, timestamp)
            return event
        except Exception as ex:
            raise ValueError(f'Failed to save job status. job_id={job_id}, status={status}.') from ex

def get_job_request_from_queue():
    try:
        logging.info('Waiting for new job request ...')
        message = run_command('./get_message_from_queue.sh')
    except Exception as ex:
        logging.error('Failed to get job request: %s', ex)
        logging.error(traceback.format_exc())
        return None

    try:
        return yaml.safe_load(message)
    except yaml.error.YAMLError as ex:
        logging.error('Failed to load YAML from queue message:\n%s', message)
        logging.error(traceback.format_exc())
        return None

def main():
    job_launcher = JobLauncher()
    job_tracker = JobTracker()
    while True:
        request = get_job_request_from_queue()
        logging.info(f'Received message:\n%s', yaml.safe_dump(request, default_flow_style=False))
        if request is None or 'job_id' not in request:
            logging.error('Missing job_id in request:\n%s', request)
            continue
        try:
            job_id = request['job_id']
            job_tracker.save_job_history(job_id, 'Dequeued', datetime.now(timezone.utc))
            job_launcher.launch_job(request)
            job_tracker.track_job(job_id)
        except Exception as ex:
            logging.error(f'Failed to handle job request for job_id={job_id}: %s', str(ex))
            logging.error(traceback.format_exc())

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
    main()
