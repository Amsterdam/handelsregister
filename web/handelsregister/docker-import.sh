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

#echo database:5432:handelsregister:handelsregister:insecure >> ~/.pgpass
#echo database:5432:atlas:handelsregister:insecure >> ~/.pgpass
#chmod 0600 ~/.pgpass
#echo copying bag vbo geo -> hr_geovbo tabel
#psql -U handelsregister -h database atlas -c  \
#'\copy (SELECT id, landelijk_id, geometrie from bag_verblijfsobject) TO STDOUT' \
#| psql -U handelsregister -h database handelsregister -c \
#'\copy hr_geovbo (id, bag_vbid, geometrie) FROM STDIN'



python /app/manage.py run_import

# autocorrect locations fields with search resultaten
# python /app/manage.py run_import --search || echo "Search failed continuing"

# create geoviews
python /app/manage.py run_import --geovestigingen



