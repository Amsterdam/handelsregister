#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error

source docker-wait.sh

python /app/manage.py test
