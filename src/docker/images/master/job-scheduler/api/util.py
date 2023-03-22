#!/usr/bin/env python3

import os, sys
import subprocess
import dataclasses
from datetime import datetime, date, timedelta, time
from enum import Enum
from typing import Any, Sequence, Union
from flask import current_app
from flask.json import JSONEncoder

def get_env_var(key):
    return os.environ[key]

def run_command_and_print_output(cmd, input=None):
    call = subprocess.run(cmd, input=input, stdout=subprocess.PIPE, text=True)
    if call.stdout:
        current_app.logger.info(call.stdout)
    if call.stderr:
        current_app.logger.info(call.stderr)
    call.check_returncode()

class CustomJSONEncoder(JSONEncoder):
    def default(self, o: object) -> Any:
        """This defines serialization for object types that `json` cannot handle by default."""
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, timedelta):
            return o.total_seconds()
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, Enum):
            return o.value
        raise TypeError(f"Type {type(o)} is not serializable")

def get_all_enum_values(enum_type):
    """Get all values of a particular Enum type."""
    return [e.value for e in enum_type]
