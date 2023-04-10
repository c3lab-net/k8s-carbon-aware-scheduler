#!/bin/sh

if [ $# -lt 1 ]; then
    echo >&2 "Usage: $0 path/to/body.json"
    exit 1
fi

json_file="$1"

if ! [ -f "$json_file" ]; then
    echo >&2 "JSON file \"$json_file\" not found."
    exit 1
fi

JOB_SCHEDULER_URL=https://cas-job-scheduler.nrp-nautilus.io/job-scheduler/

set -x

curl -X POST -H "Content-Type: application/json" -d @"$json_file" $JOB_SCHEDULER_URL
