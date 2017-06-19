#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error

echo 'Downloading latest mks dumps'
# uses data and unzipped dir
python get_mks_dumps.py

echo 'Store mks dumps in database'
source loaddumps.sh
# to test locally
# source loaddumps_local.sh

# import sbicodes
python /app/manage.py run_import --cbs_sbi

# load mks data into HR models
python /app/manage.py run_import

# autocorrect locations fields with search resultaten
python /app/manage.py run_import --search

# create geoviews
python /app/manage.py run_import --geovestigingen

# create dataselectie
python /app/manage.py run_import --dataselectie
