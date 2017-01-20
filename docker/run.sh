#!/usr/bin/env bash

# determine this files directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

docker run \
    --rm \
    -t \
    -i \
    --name aws-deployer \
    -v "$DIR/../":/deploy \
    -v /tmp/deployer:/tmp \
    -v "$(pwd)":/project \
    aws-deployer-image \
    "$@"