#!/usr/bin/env bash

if [ -n "$1" ]; then
    cd /deploy/scripts && python "./$1" "$@"
else
    cd /deploy/scripts && ls -la
fi