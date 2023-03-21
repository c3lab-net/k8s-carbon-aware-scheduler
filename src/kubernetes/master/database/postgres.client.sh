#!/bin/zsh

cd "$(dirname "$0")"

yaml_file=postgres.client.yaml
image="$(cat $yaml_file | yq '.spec.containers[0].image')"
random_name="$(cat /dev/urandom | tr -cd 'a-f0-9' | head -c 8)"
json_override="$(cat $yaml_file | yq -o=json)"

kubectl run -i --rm --tty postgres-client-"$random_name" \
            --overrides="$json_override" \
            --image="$image" --restart=Never
