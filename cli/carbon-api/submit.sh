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

CARBON_API_URL=https://cas-carbon-api-dev.nrp-nautilus.io/carbon-aware-scheduler/
# CARBON_API_URL=http://localhost:8082/carbon-aware-scheduler/

set -x

curl -s -X GET -H "Content-Type: application/json" -d @"$json_file" $CARBON_API_URL | jq
