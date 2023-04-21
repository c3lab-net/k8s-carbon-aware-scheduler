#!/usr/bin/env python3

from typing import Optional
from flask import current_app
from flask_restful import Resource
from webargs.flaskparser import use_args
from marshmallow import validates_schema, ValidationError
import marshmallow_dataclass
from marshmallow_dataclass import dataclass

from api.helpers.postgres import *
from api.models.dataclass_extensions import *


@dataclass
class JobStatusRequest:
    job_id: Optional[str] = field(default=None)
    job_name: Optional[str] = field(default=None)

    @validates_schema
    def validate_schema(self, data, **kwargs):
        errors = dict()
        if 'job_id' not in data and 'job_name' not in data:
            error_message_either_id_or_name_is_required = 'Either job_id or job_name is required'
            errors['job_id'] = error_message_either_id_or_name_is_required
            errors['job_name'] = error_message_either_id_or_name_is_required
        if errors:
            raise ValidationError(errors)


class JobStatus(Resource):
    def __init__(self):
        super().__init__()
        self.dbconn = get_db_connection(autocommit=True)

    @use_args(marshmallow_dataclass.class_schema(JobStatusRequest)(), location='query')
    def get(self, args: JobStatusRequest):
        if args.job_id:
            job_status = self._get_job_status(job_id=args.job_id)
        else:
            job_status = self._get_job_status(job_name=args.job_name)
        return job_status

    def _get_job_status(self, job_id: str = None, job_name: str = None):
        job_description = f'job_id={job_id}' if job_id else f'job_name={job_name}'
        if job_id:
            current_app.logger.info(f'Getting job status with {job_description}')
        else:
            current_app.logger.info(f'Getting job status with {job_description}')
        try:
            cursor = self.dbconn.cursor()
            if job_id:
                result = psql_execute_list(
                    cursor,
                    'SELECT job_id, event, time FROM JobHistoryLastEvent WHERE job_id = %s;',
                    [ job_id ],
                    fetch_result=True)
            else:
                result = psql_execute_list(
                    cursor,
                    """SELECT event.job_id, event.event, event.time
                        FROM JobHistoryLastEvent event INNER JOIN JobRequest jobs
                            ON event.job_id = jobs.job_id
                        WHERE jobs.name = %s;""",
                    [ job_name ],
                    fetch_result=True)
            current_app.logger.debug(result)
            assert len(result) == 1, 'Should not have more than one row'
            row = result[0]
            return {
                'job_id': row[0],
                'event': row[1],
                'timestamp': row[2],
            }
        except Exception as ex:
            raise ValueError(f'Failed to get job status ({job_description}).') from ex
