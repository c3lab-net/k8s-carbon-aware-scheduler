#!/usr/bin/env python3

import json
import sys
from shlex import quote

from util import run_command, get_random_name

class RcloneHelper:
    """Helper class that runs rclone commands."""
    def __init__(self) -> None:
        print("Initializing rclone helper ...")
        try:
            rclone_version = run_command('rclone version').splitlines()[0]
            print(f'rclone installed: {rclone_version}', file=sys.stderr)
        except ValueError as ex:
            raise ValueError('rclone not installed') from ex

    def create_bucket(self, endpoint: str = "us-west", name: str = None):
        """Create a new bucket."""
        if not name:
            name = f'tmp.{get_random_name()}'
        print(run_command(f'rclone mkdir {quote(endpoint)}:{quote(name)}', print_command=True))
        return (endpoint, name)

    def delete_bucket(self, endpoint: str = "us-west", name: str = None):
        """Delete a bucket."""
        print(run_command(f'rclone purge {quote(endpoint)}:{quote(name)}', print_command=True))

    def sync(self, src_path: str, dst_path: str):
        """Sync src to dst using rclone."""
        print(run_command(f'rclone sync {quote(src_path)} {quote(dst_path)}', print_command=True))

    def get_size(self, path: str) -> int:
        """Get the size of a directory."""
        json_str = run_command(f'rclone size {quote(path)} --json')
        try:
            json_object = json.loads(json_str)
        except Exception as ex:
            raise ValueError(f'Unable to decode json output "{json_str}"') from ex
        return json_object['bytes']
