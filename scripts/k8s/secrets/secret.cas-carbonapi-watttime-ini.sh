#!/bin/sh

kubectl create secret generic cas-carbonapi-watttime-ini --from-file=watttime.ini

# Use kubectl edit secrets and add `immutable: true` to prevent further changes
