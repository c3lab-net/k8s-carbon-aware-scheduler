#!/usr/bin/env python3

import requests

from api.models.job_request import JobLocation

class CarbonApiClient:
    def __init__(self):
        self.session = requests.Session()

    def get_carbon_emissions_by_location(self, original_location: str, candidate_locations: list[JobLocation], input_size_gb: int = 0, output_size_gb: int = 0) -> list:
        raise NotImplementedError()
