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

# Load all sql files
# Ignore lines which match certain patterns (grep)
# or replace values with '' (sed)
for sql in *.sql; do
    echo "Filtering $sql"
    grep -v OWNER $sql | grep -v search_path | grep -v REVOKE |  \
    grep -v ^GRANT | \
    grep -v "CREATE TRIGGER" | \
    grep -v ^DROP | \
    grep -v "CREATE INDEX" | \
    grep -v "ADD CONSTRAINT" | \
    grep -v "ALTER TABLE" | \
    grep -v "PRIMARY KEY (" | \
    grep -v "^SET default_table_access_method" | \
    sed 's/^.*geometry(Point.*$/    geopunt GEOMETRY(Point,28992)/' | \
    sed -r 's/igp_[a-zA-Z0-9_]+_cmg_owner\.//' | \
    psql -v ON_ERROR_STOP=1 -d handelsregister -h database -U handelsregister
done

# PUT BAVK WD! ^*&^*^
cd /app/
