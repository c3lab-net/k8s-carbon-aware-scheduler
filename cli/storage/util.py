#!/usr/bin/env python3

import uuid
import sys
import subprocess
from subprocess import PIPE, STDOUT
import shlex
import yaml

def load_yaml(path):
    """Load a YAML file."""
    with open(path, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as ex:
            raise ValueError(f'Failed to load YAML file "{path}"') from ex

def load_file_as_str(path):
    """Load a file and return its content as a string."""
    with open(path, 'r') as f:
        return f.read()

def run_command(args: str, stdin: str = None, print_command=False) -> str:
    """Run a given command and return combined stdout and stderr.

        Args:
            args: a space-separated command. Parameters must be quoted using shlex.quote().
            stdin: an optional string to pass to stdin.
            print_command: whether to print the command ran.
    """
    args = shlex.split(args)
    if print_command:
        print(f"+ {shlex.join(args)}", file=sys.stderr)
        if stdin:
            print(stdin, file=sys.stderr)
    process = subprocess.run(args, input=stdin, stdout=PIPE, stderr=STDOUT,
                                check=False, text=True)
    try:
        process.check_returncode()
    except subprocess.CalledProcessError as ex:
        raise ValueError(f'Failed to run command "{args}":'
                            f'{process.stdout}') \
            from ex
    return process.stdout

def get_random_name():
    """Get a random name."""
    return uuid.uuid4().hex
