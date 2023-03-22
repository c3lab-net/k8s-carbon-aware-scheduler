#!/usr/bin/env python3

import time
import random
from datetime import datetime
from flask import current_app

from api.util import get_env_var, run_command_and_print_output
from api.config import *

class JobQueue:
    def __init__(self, regions=REGIONS):
        self.regions = regions
        # self._init_job_queues()

    def _init_job_queues(self):
        for region in self.regions:
            current_app.logger.info(f"Declaring queue for region {region} ...")
            run_command_and_print_output([
                "/usr/bin/amqp-declare-queue",
                "--url", BROKER_URL,
                "-q", self._get_queue_name(region),
                "-d"
            ])
            self.send_message_to_region(region, 'Startup')

    def _get_queue_name(self, region: str) -> str:
        return f"{QUEUE_PERFIX}.{region}"


    def send_message_to_region(self, region: str, message: str):
        current_app.logger.info(f"Sending message to region {region}, len = {len(message)} ...")
        run_command_and_print_output([
                "/usr/bin/amqp-publish",
                "--url", BROKER_URL,
                "-r", self._get_queue_name(region),
                "-p"
            ], message)
