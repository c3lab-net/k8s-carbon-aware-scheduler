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

def save_job_status(job_id, status):
    logging.info(f'Saving job {job_id} status: {status}')
    try:
        conn = get_db_connection()
        with conn, conn.cursor() as cursor:
            if 'completionTime' in status:
                psql_execute_list(cursor, 'INSERT INTO JobHistory VALUES', [
                    (job_id, 'Complete', status['completionTime'])
                ])
            elif 'startTime' in status:
                psql_execute_list(cursor, 'INSERT INTO JobHistory VALUES', [
                    (job_id, 'Start', status['startTime'])
                ])
            else:
                logging.error(f'Unhandled status: {json.dumps(status)}')
                psql_execute_list(cursor, 'INSERT INTO JobHistory VALUES', [
                    (job_id, 'Unknown', datetime.now(tz=timezone.utc))
                ])
    except Exception as ex:
        raise ValueError(f'Failed to save job status. job_id={job_id}, status={status}.') from ex

def main():
    request = read_stdin()
    logging.info(f'Received message:\n%s', yaml.safe_dump(request, default_flow_style=False))
    assert 'job_id' in request, 'Missing job_id in request:\n' + request
    try:
        job_config = create_job_config(request)
        status = create_job(job_config)
        save_job_status(request['job_id'], status)
    except Exception as ex:
        logging.error('Failed to handle job request: %s', str(ex))
        logging.error(traceback.format_exc())
        # save_job_status(request['job_id'], str(ex))

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
    main()
