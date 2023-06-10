#!/bin/bash

if [ $# -lt 3 ]; then
    echo >&2 "Usage: $0 secret-name src-namespace dst-namespace"
    exit 1
fi

secretname="$1"
src_ns="$2"
dst_ns="$3"

kubectl get secret "$secretname" --namespace="$src_ns" -o yaml | grep -v '^\s*namespace:\s' |  kubectl apply --namespace="$dst_ns" -f -
