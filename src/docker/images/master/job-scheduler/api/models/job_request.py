#!/usr/bin/env python3

import re
from datetime import timedelta
from enum import Enum
from typing import Optional, Tuple

from marshmallow import validates_schema, ValidationError
from marshmallow_dataclass import dataclass

from api.util import get_env_var
from api.config import REGIONS as AVAILABLE_LOCATIONS
from api.models.dataclass_extensions import *

PATTERN_REGION = "|".join(map(re.escape, AVAILABLE_LOCATIONS))
REGEX_BY_STORAGE_TYPE: dict[str, re.Pattern] = {
    'pvc': re.compile(r'^pvc://([\w.-]+)/?$'),
    's3': re.compile(rf'^s3://({PATTERN_REGION}):([\w.-]+(?:\/[\w.-]+)*\/?)$'),
}

def parse_storage_url(url: str) -> tuple[str, list[str]]:
    for storage_type, regex in REGEX_BY_STORAGE_TYPE.items():
        m = regex.match(url)
        if not m:
            continue
        return storage_type, m.groups()
    return None, []

def is_valid_mountpoint(path: str) -> bool:
    regex = re.compile(r'^(?:\/[\w.-]+)*\/?$')
    return regex.match(path) is not None

def is_valid_storage_url(url: str) -> bool:
    storage, _ = parse_storage_url(url)
    return storage is not None

def validate_mountpoints(d: dict[str, str]) -> bool:
    errors = []
    for mountpoint, url in d.items():
        if not is_valid_mountpoint(mountpoint):
            errors.append(f'Invalid mountpoint "{mountpoint}"')
        if not is_valid_storage_url(url):
            errors.append(f'Invalid URL for mounpoint "{mountpoint}": "{url}"')
    if len(errors) > 0:
        raise ValidationError('\n'.join(errors))
    else:
        return True

def is_valid_name(name: str) -> bool:
    regex = re.compile(r'^[\w_.-]+$')
    return regex.match(name) is not None

def is_valid_image_name(name: str) -> bool:
    regex = re.compile(r'^[\w_./:-]+$')
    return regex.match(name) is not None

@dataclass
class JobSpec:
    name: str = field_with_validation(is_valid_name)
    image: str = field_with_validation(is_valid_image_name)
    command: list[str] = field()
    max_delay: timedelta = field(metadata=metadata_timedelta_nonzero)

@dataclass
class JobLocation:
    location_id: str
    latitude: float = field_with_validation(validate.Range(-90., 90.))
    longitude: float = field_with_validation(validate.Range(-180., 180.))

def is_valid_resource_cpu(cpu: str|int) -> bool:
    # Source: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu
    if cpu is int:
        return True
    regex = re.compile(r'^[0-9.]+m?$')
    return regex.match(cpu) is not None

def is_valid_resource_memory(memory: str|int) -> bool:
    # Source: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory
    if memory is int:
        return True
    regex = re.compile(r'^[0-9.]+(?:e-?[0-9]+)?(?:E|P|T|G|M|k|Ei|Pi|Ti|Gi|Mi|Ki)?$')
    return regex.match(memory) is not None

@dataclass
class ContainerResource:
    cpu: str|int = field_with_validation(is_valid_resource_cpu)
    memory: str|int = field_with_validation(is_valid_resource_memory)

@dataclass
class ContainerResourceRequirement:
    requests: ContainerResource
    limits: ContainerResource

@dataclass
class JobRequest:
    spec: JobSpec
    original_location: Optional[str] = field_with_validation(validate.OneOf(AVAILABLE_LOCATIONS))
    resources: Optional[ContainerResourceRequirement]
    inputs: dict[str, str] = field_with_validation(validate_mountpoints)
    outputs: dict[str, str] = field_with_validation(validate_mountpoints)

    @validates_schema
    def validate_input_output_nonoverlapping(self, data, **kwargs):
        errors = dict()
        if set(data['inputs'].keys()).intersection(set(data['outputs'].keys())):
            error_message_duplicate_keys = 'Duplicate keys in inputs and outputs dictionary.'
            errors['inputs'] = error_message_duplicate_keys
            errors['outputs'] = error_message_duplicate_keys
        if errors:
            raise ValidationError(errors)

    def get_parsed_mountpoints(self, input_or_output: dict[str, str]):
        parsed_mountpoints = {}
        for mountpoint, url in input_or_output:
            storage_type, paths = parse_storage_url(url)
            parsed_mountpoints[mountpoint] = {
                'storage_type': storage_type,
                'paths': paths,
            }
        return parsed_mountpoints
