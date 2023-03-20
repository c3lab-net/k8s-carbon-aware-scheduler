#!/bin/zsh

kubectl create secret generic cas-master-database \
    --from-literal=POSTGRES_DB='casjobscheduler' \
    --from-literal=POSTGRES_USER='casuser' \
    --from-literal=POSTGRES_PASSWORD='insert-password-here'
