#!/usr/bin/env python3

import os
import sys
import yaml
import logging
import shlex
import subprocess
from subprocess import PIPE, STDOUT
from typing import Any
from threading import Timer

def get_env_var(key):
    return os.environ[key]

def load_yaml(path):
    """Load a YAML file."""
    with open(path, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as ex:
            raise ValueError(f'Failed to load YAML file "{path}"') from ex

def run_command(args: str, stdin: str = None, print_command=False) -> str:
    """Run a given command and return combined stdout and stderr.

        Args:
            args: a space-separated command. Parameters must be quoted using shlex.quote().
            stdin: an optional string to pass to stdin.
            print_command: whether to print the command ran.
    """
    args = shlex.split(args, posix=False)
    print_fn = logging.info if print_command else logging.debug
    print_fn(f"+ {shlex.join(args)}")
    if stdin:
        print_fn(stdin)
    process = subprocess.run(args, input=stdin, stdout=PIPE, stderr=STDOUT,
                                check=False, text=True)
    try:
        process.check_returncode()
    except subprocess.CalledProcessError as ex:
        raise ValueError(f'Failed to run command "{args}":'
                            f'{process.stdout}') \
            from ex
    return process.stdout

def get_dict_value_or_default(d: dict, key: Any, default: Any) -> Any:
    return d[key] if key in d else default

class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
