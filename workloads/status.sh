#!/bin/sh

while [ $# -gt 0 ]; do
case $1 in
  --job_id)
    shift
    job_id="$1"
    shift
    ;;
    --job_name)
    shift
    job_name="$1"
    shift
    ;;
  *)
    echo >&2 "Ignoring unknown argument \"$1\" ..."
    shift
    ;;
esac
done

if [ -z $job_id ] && [ -z $job_name ]; then
    echo >&2 "Usage: $0 --job_id <job_id> or $0 --job_name <job_name>"
    exit 1
fi

JOB_SCHEDULER_URL=https://cas-job-scheduler.nrp-nautilus.io/job-status/

[ -z $job_id ] || args="job_id=$job_id"
[ -z $job_name ] || args="job_name=$job_name"

set -x

curl -s "$JOB_SCHEDULER_URL?$args" | jq
