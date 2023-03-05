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

def is_valid_path(path: str) -> bool:
    regex = re.compile(r'^(?:\/[\w.-]+)*\/?$')
    return regex.match(path) is not None

def is_valid_s3_url(url: str) -> bool:
    pattern_region = "|".join(map(re.escape, AVAILABLE_LOCATIONS))
    charset = r'[\w._-]+'
    regex = re.compile(rf'^s3://({pattern_region}):({charset})((?:\/{charset})*\/?)$')
    return regex.match(url) is not None

def validate_mountpoints(d: dict[str, str]) -> bool:
    errors = []
    for path, url in d.items():
        if not is_valid_path(path):
            errors.append(f'Invalid path "{path}"')
        if not is_valid_s3_url(url):
            errors.append(f'Invalid URL for "{path}": {url}')
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

@dataclass
class JobRequest:
    spec: JobSpec
    original_location: Optional[str] = field_with_validation(validate.OneOf(AVAILABLE_LOCATIONS))
    inputs: dict[str, str] = field_with_validation(validate_mountpoints)
    outputs: dict[str, str] = field_with_validation(validate_mountpoints)
