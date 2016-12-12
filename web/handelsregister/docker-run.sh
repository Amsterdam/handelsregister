#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error

source docker-wait.sh

source docker-migrate.sh || echo "Could not migrate, ignoring"

echo Collecting static files
yes yes | python manage.py collectstatic || echo "Could not loac static content, ignoring"

# run uwsgi
exec uwsgi --ini /app/uwsgi.ini
