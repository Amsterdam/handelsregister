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
echo database:5432:handelsregister:handelsregister:insecure >> ~/.pgpass
echo database:5432:atlas:handelsregister:insecure >> ~/.pgpass
chmod 0600 ~/.pgpass
echo copying bag vbo geo -> hr_geovbo tabel
psql -U handelsregister -h database atlas -c  \
	| psql -U handelsregister -h database handelsregister -c \

# add health check?
python /app/manage.py run_import

# autocorrect locations fields with search resultaten
python /app/manage.py run_import --search || echo "Search failed, continuing anyway"

# create geoviews
python /app/manage.py run_import --geovestigingen



