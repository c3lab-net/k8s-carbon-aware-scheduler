#!/bin/bash

cd "$(dirname "$0")/../../../src/kubernetes" || { echo >&2 "Cannot cd to kubernetes directory."; exit 1; }

find . -type f -name '*.deployment.yaml' -exec kubectl delete -f {} \;
