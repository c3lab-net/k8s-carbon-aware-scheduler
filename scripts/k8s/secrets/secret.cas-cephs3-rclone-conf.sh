#!/bin/sh

RCLONE_CONF_FILE="$(rclone config file | grep rclone.conf$)"
kubectl create secret generic cas-cephs3-rclone-conf --from-file=rclone.conf="$RCLONE_CONF_FILE"

# Use kubectl edit secrets and add `immutable: true` to prevent further changes
