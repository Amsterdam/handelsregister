#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error

python /app/manage.py loaddata /app/datasets/kvkdump/fixture_files/hcat.json
python /app/manage.py loaddata /app/datasets/kvkdump/fixture_files/scat.json
python /app/manage.py loaddata /app/datasets/kvkdump/fixture_files/sbicodes.json
