#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error

source docker-wait.sh

source docker-migrate.sh

echo 'Downloading latest mks dumps'
python get_mks_dumps.py

echo 'Store mks dumps in database'
source loaddumps.sh

echo 'Copy bag geometrie naar hg_geobag'

source copy_bagvbo_to_hr.sh

# load mks data into HR models
python /app/manage.py run_import

# autocorrect locations fields with search resultaten
python /app/manage.py run_import --search || echo "Search failed, continuing anyway"

# import sbicodes
python /app/manage.py run_import --cbs_sbi || echo "CBS import failed, continuing anyway"

# create geoviews
python /app/manage.py run_import --geovestigingen || echo "Geovestigingen build failed, continuing anyway"

# create dataselectie export
python /app/manage.py run_import --dataselectie || echo "Dataselectie build failed, continuing anyway"
