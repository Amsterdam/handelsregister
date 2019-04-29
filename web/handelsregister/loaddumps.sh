#!/bin/bash

set -e
set -u

# wait for database to load
source docker-wait.sh

echo 'extracting latest kvk dump files'

for f in data/*.gz; do
    STEM=$(basename "${f}" .gz)
    gunzip -c "${f}" > unzipped/"${STEM}"
done

psql -d handelsregister -h database -U handelsregister -f dropallkvk.sql

cd /app/unzipped/

#Load all sql files

for sql in *.sql; do
    grep -v OWNER $sql | grep -v search_path | grep -v REVOKE |  \
    grep -v ^GRANT | \
    grep -v "CREATE TRIGGER" | \
    grep -v ^DROP | \
    grep -v "CREATE INDEX" | \
    grep -v "ADD CONSTRAINT" | \
    grep -v "ALTER TABLE" | \
    grep -v "PRIMARY KEY (" | \
    sed 's/^.*geometry(Point.*$/    geopunt GEOMETRY(Point,28992)/' | \
    sed 's/igp_sw44z0001_cmg_owner\.//' | \
    psql -v ON_ERROR_STOP=1 -d handelsregister -h database -U handelsregister
done

# PUT BAVK WD! ^*&^*^
cd /app/
