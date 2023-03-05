#!/usr/bin/env python3

from flask import current_app
from flask_restful import Resource
from webargs.flaskparser import use_args
import marshmallow_dataclass
import yaml

from api.models.job_request import JobRequest
from api.helpers.carbon_api_client import CarbonApiClient
from api.helpers.job_queue import JobQueue
from api.config import REGIONS as AVAILABLE_LOCATIONS

g_carbon_api_client = CarbonApiClient()
g_job_queue = JobQueue()


class JobSchduler(Resource):
    def __init__(self):
        super().__init__()

    @use_args(marshmallow_dataclass.class_schema(JobRequest)())
    def post(self, job_request: JobRequest):
        current_app.logger.info(f'{__class__}.post({job_request})')
        best_location = self._get_best_location(job_request)
        self._send_job_to_queue(best_location, yaml.dump(job_request))
        # TODO: wait for response, or return a request id
        return {}, 201

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

    def _send_job_to_queue(self, region, message):
        try:
            g_job_queue.send_message_to_region(region, message)
        except Exception as ex:
            raise ValueError('Failed to send job to queue') from ex

    def _get_data_size(self, name: str, mountpoints: dict[str, str]) -> float:
        # NOTE: keep track of historic size, or probe for estimated size.
        return 0.
