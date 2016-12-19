#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error

source docker-wait.sh
yes yes | python manage.py migrate geo_views zero --noinput
yes yes | python manage.py migrate --noinput
