#!/usr/bin/env -S python3 -u

import os, sys
import time
import random
import subprocess
from datetime import datetime

print("Job scheduler starting ...")

def get_env_var(key):
    return os.environ[key]

BROKER_URL = get_env_var("BROKER_URL")
QUEUE_PERFIX = get_env_var("QUEUE_PERFIX")
REGIONS = get_env_var("REGIONS").split(":")

def run_command_and_print_output(cmd, input=None):
    call = subprocess.run(cmd, input=input, stdout=subprocess.PIPE, text=True)
    if call.stdout:
        print(call.stdout)
    if call.stderr:
        print(call.stderr, file=sys.stderr)
    call.check_returncode()

def get_queue_name(region: str) -> str:
    return f"{QUEUE_PERFIX}.{region}"

def declare_queues():
    for region in REGIONS:
        print(f"Declaring queue for region {region} ...")
        run_command_and_print_output([
            "/usr/bin/amqp-declare-queue",
            "--url", BROKER_URL,
            "-q", get_queue_name(region),
            "-d"
        ])

def send_message_to_region(region: str, message: str):
    print(f"Sending message to region {region}, len = {len(message)} ...")
    run_command_and_print_output([
            "/usr/bin/amqp-publish",
            "--url", BROKER_URL,
            "-r", get_queue_name(region),
            "-p"
        ], message)

def main():
    declare_queues()
    for _ in range(1000):
        time.sleep(random.randint(5, 10))
        region = REGIONS[random.randint(0, len(REGIONS) - 1)]
        print("Sending test jobs to region %s ..." % region)
        send_message_to_region(region, "Test message sent at " + datetime.utcnow().isoformat())

if __name__ == "__main__":
    main()
