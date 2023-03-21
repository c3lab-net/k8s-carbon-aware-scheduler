#!/bin/zsh

cd "$(dirname "$0")" || exit 1

BUILD_SCRIPT="$(realpath ../../build.sh)"

VERSION="0.1"

set -e

build_image()
{
    PROJECT_NAME="$1"
    IMAGE_NAME="$2"
    IMAGE_VERSION="${3}"

    FULL_IMAGE_NAME=gitlab-registry.nrp-nautilus.io/c3lab/$PROJECT_NAME/$IMAGE_NAME:$IMAGE_VERSION

    echo "Building image $FULL_IMAGE_NAME ..."
    (set -x; docker build -t $FULL_IMAGE_NAME .)

    echo Done
    echo "Run this to push to registry:"
    echo "docker push $FULL_IMAGE_NAME"
}

cwd="$(pwd)"
for f in **/Dockerfile; do
    relpath=$(dirname "$f")
    component="${relpath:gs/\//.}"
    cd "$relpath" && build_image carbon-aware-scheduler "$component" "$VERSION"
    cd "$cwd"
done
