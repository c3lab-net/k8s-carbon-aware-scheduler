#!/bin/sh

kubectl create secret generic cas-carboncast-rdams-client \
    --from-literal=rdams_client_username='insert-username-here' \
    --from-literal=rdams_client_password='insert-password-here'
