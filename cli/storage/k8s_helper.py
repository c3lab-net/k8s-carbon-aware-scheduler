#/usr/bin/env python3

import os
import json
import sys
from time import sleep
from shlex import quote

from pvc import exist_pvc, create_pvc
from util import run_command, load_file_as_str, get_random_name

class K8sHelper:
    """A helper tool that runs kubernetes (k8s) commands."""
    def __init__(self) -> None:
        print("Initializing kubernetes (k8s) helper ...")
        try:
            kubectl_version = run_command('kubectl version --short')
            print(f'kubectl installed:\n{kubectl_version}', file=sys.stderr)
        except ValueError as ex:
            raise ValueError('kubectl not installed') from ex
        self.templates = {}
        self.templates['s3_pvc_transfer'] = load_file_as_str(
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            "k8s.transfer.s3_pvc.template.yaml"))

    def _is_job_completed(self, job_name: str) -> object:
        """Return whether the job completed successfully."""
        json_str = run_command(f'kubectl get job {quote(job_name)} ' +
                            quote('-o=jsonpath={.status}'), print_command=False)
        try:
            job_status = json.loads(json_str)
        except Exception as ex:
            raise ValueError(f'Unable to decode json output "{json_str}"') from ex
        if 'completionTime' not in job_status:
            return False
        if 'succeeded' in job_status and job_status['succeeded'] is not None:
            return True
        raise ValueError(f'Cannot parse job status {job_status}')

    def _run_s3_pvc_transfer_job(self, pvc_name, src_path, dst_path):
        """Invoke an s3/pvc data transfer job and wait till it finishes."""
        job_name = f's3-pvc-transfer-{get_random_name()}'
        vars_to_substitute = {
            'VAR_job_name': job_name,
            'VAR_pvc_name': pvc_name,
            'VAR_src': src_path,
            'VAR_dst': dst_path,
        }
        job_config = self.templates['s3_pvc_transfer']
        for var_name, value in vars_to_substitute.items():
            job_config = job_config.replace(var_name, value)
        print("Running an s3/pvc data transfer job ...")
        print(run_command('kubectl create -f -', job_config, print_command=True))
        print("Waiting for the data transfer job to finish ...")
        while True:
            job_completed = self._is_job_completed(job_name)
            print(f'Completed: {job_completed}')
            if job_completed:
                break
            wait_seconds = 10
            print(f'Sleeping for {wait_seconds}s ...')
            sleep(wait_seconds)
        print(f's3/pvc data transfer job {job_name} completed.')
        # print(run_command(f'kubectl delete job {quote(job_name)}', print_command=True))

    def sync_s3_to_pvc(self, src: str, dst: str, size: int):
        """Sync from S3 to PVC."""
        (dst_pvc_name, dst_path_in_pvc) = dst.split(':', 2)
        if not exist_pvc(dst_pvc_name):
            print('Destination PVC does not exist. Creating ...')
            create_pvc(dst_pvc_name, str(int(size * 1.2)))
        self._run_s3_pvc_transfer_job(dst_pvc_name, src, dst_path_in_pvc)

    def sync_pvc_to_s3(self, src: str, dst: str):
        """Sync from PVC to S3."""
        (src_pvc_name, src_path_in_pvc) = src.split(':', 2)
        self._run_s3_pvc_transfer_job(src_pvc_name, src_path_in_pvc, dst)

    def sync_pvc_to_pvc(self, src: str, dst: str):
        """Sync from a PVC path to another PVC path."""
        raise NotImplementedError('Currently not implemented')
