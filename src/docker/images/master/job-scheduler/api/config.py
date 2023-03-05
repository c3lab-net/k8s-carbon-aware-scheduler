#!/usr/bin/env python3

from api.util import get_env_var

BROKER_URL = get_env_var("BROKER_URL")
QUEUE_PERFIX = get_env_var("QUEUE_PERFIX")
REGIONS = get_env_var("REGIONS").split(":")
CARBON_API_ENDPOINT = get_env_var("CARBON_API_ENDPOINT")

assert len(REGIONS) > 0, 'Must have at least one region'
