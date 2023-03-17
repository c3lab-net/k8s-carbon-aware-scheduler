#!/bin/sh

kubectl create secret generic cas-serviceaccount --from-file=config="$HOME/.kube/config_sa.sched.carbonaware"

# Use kubectl edit secrets and add `immutable: true` to prevent further changes
