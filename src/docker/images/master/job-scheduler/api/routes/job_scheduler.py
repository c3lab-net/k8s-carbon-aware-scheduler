#!/usr/bin/env python3

import uuid
from datetime import datetime, timezone
from flask import current_app
from flask_restful import Resource
from webargs.flaskparser import use_args
import marshmallow_dataclass
import yaml

from api.models.job_request import JobRequest
from api.helpers.carbon_api_client import CarbonApiClient
from api.helpers.job_queue import JobQueue
from api.helpers.postgres import *
from api.config import REGIONS as AVAILABLE_LOCATIONS

g_carbon_api_client = CarbonApiClient()
g_job_queue = JobQueue()


class JobSchduler(Resource):
    def __init__(self):
        super().__init__()
        self.dbconn = get_db_connection(autocommit=True)

    def __del__(self):
        self.dbconn.close()

    @use_args(marshmallow_dataclass.class_schema(JobRequest)())
    def post(self, job_request: JobRequest):
        current_app.logger.info(f'{__class__}.post({job_request})')
        job_id = str(uuid.uuid4())
        self._save_job_request(job_id, job_request)
        self._save_job_history(job_id, 'Created', datetime.now(timezone.utc))
        best_location = self._get_best_location(job_request)
        job_message = {
            'job_id': job_id,
            'name': job_request.spec.name,
            'image': job_request.spec.image,
            'command': job_request.spec.command,
            # 'max_delay': job_request.spec.max_delay,
            'inputs': job_request.get_parsed_mountpoints(job_request.inputs),
            'outputs': job_request.get_parsed_mountpoints(job_request.outputs),
        }
        if job_request.resources:
            job_message |= {
                'resources.requests.cpu': job_request.resources.requests.cpu,
                'resources.requests.memory': job_request.resources.requests.memory,
                'resources.limits.cpu': job_request.resources.limits.cpu,
                'resources.limits.memory': job_request.resources.limits.memory,
            }
        self._send_job_to_queue(best_location, yaml.safe_dump(job_message, default_flow_style=False))
        self._save_job_history(job_id, 'Enqueued', datetime.now(timezone.utc))
        # TODO: wait for response, or return a request id
        return {
            'job_id': job_id,
        }, 201

    def _get_best_location(self, job_request: JobRequest):
        try:
            emissions_by_location = g_carbon_api_client.get_carbon_emissions_by_location(
                job_request.original_location,
                AVAILABLE_LOCATIONS,
                self._get_data_size(job_request.spec.name, job_request.inputs),
                self._get_data_size(job_request.spec.name, job_request.inputs)
            )
            return min(emissions_by_location, key=lambda k: emissions_by_location[k]['total_emission'])
        except Exception:
            current_app.logger.warning('Failed to obtain best location to run job, returning default ...', exc_info=True)
            return AVAILABLE_LOCATIONS[0]

    def _save_job_request(self, job_id, job_request: JobRequest):
        current_app.logger.info(f'Saving job request with job_id={job_id}:\n{yaml.dump(job_request)}')
        try:
            cursor = self.dbconn.cursor()
            result = psql_execute_values(cursor, 'INSERT INTO JobRequest (job_id, name, image, command, max_delay) VALUES %s', [
                (job_id, job_request.spec.name, job_request.spec.image, ' '.join(job_request.spec.command), job_request.spec.max_delay)
            ])
            current_app.logger.debug(result)
        except Exception as ex:
            raise ValueError(f'Failed to save job request (job_id={job_id}).') from ex

    def _save_job_history(self, job_id: str, event: str, timestamp: datetime):
        current_app.logger.info(f'Saving job history with job_id={job_id}, event={event}, timestamp={timestamp}')
        try:
            cursor = self.dbconn.cursor()
            result = psql_execute_list(cursor, 'INSERT INTO JobHistory (job_id, event, time) VALUES (%s, %s, %s)', [
                job_id, event, timestamp
            ])
            current_app.logger.debug(result)
        except Exception as ex:
            raise ValueError(f'Failed to save job history (job_id={job_id}).') from ex

    def _send_job_to_queue(self, region, message):
        try:
            g_job_queue.send_message_to_region(region, message)
        except Exception as ex:
            raise ValueError('Failed to send job to queue') from ex

    def _get_data_size(self, name: str, mountpoints: dict[str, str]) -> float:
        # NOTE: keep track of historic size, or probe for estimated size.
        return 0.
