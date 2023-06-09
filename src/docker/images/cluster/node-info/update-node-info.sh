#!/bin/zsh

cd "$(dirname "$0")"

# Run this occasionally to update the node info
kubectl get nodes -o=json | jq '.items[]' | jq -r '[.metadata.name, .metadata.labels["topology.kubernetes.io/region"], .metadata.labels["topology.kubernetes.io/zone"]] | @csv' > ./src/nodes.csv
