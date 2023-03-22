#!/usr/bin/env -S python3 -u

import os
import yaml
import logging
import json
from shlex import quote
import traceback
from datetime import datetime, timezone

from util import *
from postgres import *

def get_job_template():
    return load_yaml(os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'job.template.yaml'))

def create_job_config(request):
    logging.info('Creating job config ...')
    job_id = request['job_id']
    job_config = get_job_template()
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
    for mount_path, pvc_name in request['inputs'] | request['outputs']:
        volume_mounts.append({
            'name': pvc_name,
            'mountPath': mount_path,
        })
    container['volumeMounts'] = volume_mounts
    job_config['spec']['template']['spec']['containers'][0] = container
    return job_config

def create_job(job_config):
    logging.info('Creating job using kubectl ...')
    job_yaml = yaml.dump(job_config)
    print(run_command('kubectl create -f -', job_yaml, print_command=True))

    job_name = job_config['metadata']['name']
    result = run_command(f'kubectl get job {quote(job_name)} ' +
                            quote('-o=jsonpath={.status}'), print_command=False)
    return json.loads(result)

def save_job_history(job_id: str, event: str, timestamp: datetime):
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

def save_job_from_status_json(job_id, status):
    logging.info(f'kubectl job status for {job_id}: {status}')
    try:
        if 'completionTime' in status:
            save_job_history(job_id, 'Complete', status['completionTime'])
        elif 'startTime' in status:
            save_job_history(job_id, 'Started', status['startTime'])
        else:
            logging.error(f'Unhandled status for job {job_id}: {json.dumps(status)}')
            save_job_history(job_id, 'Unknown', datetime.now(tz=timezone.utc))
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
    while True:
        request = get_job_request_from_queue()
        logging.info(f'Received message:\n%s', yaml.safe_dump(request, default_flow_style=False))
        if request is None or 'job_id' not in request:
            logging.error('Missing job_id in request:\n%s', request)
            continue
        job_id = request['job_id']
        try:
            save_job_history(job_id, 'Dequeued', datetime.now(timezone.utc))
            job_config = create_job_config(request)
            status = create_job(job_config)
            save_job_from_status_json(job_id, status)
        except Exception as ex:
            logging.error(f'Failed to handle job request for job_id={job_id}: %s', str(ex))
            logging.error(traceback.format_exc())
            # save_job_status(job_id, str(ex))

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
    main()
