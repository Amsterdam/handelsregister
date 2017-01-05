#!/bin/bash

set -e
set -u

# wait for database to load
source docker-wait.sh

echo 'unzipping latest kvk dump files'

unzip -o $(ls -Art data/*.zip | tail -n 1) -d /app/unzipped/

psql -d handelsregister -h ${DATABASE_PORT_5432_TCP_ADDR} -U handelsregister -f dropallkvk.sql

cd /app/unzipped/

# extract gz files if needed
gunzip -f *.gz

#Load all sql files

for sql in *.sql; do
    grep -v OWNER $sql | grep -v search_path | grep -v REVOKE |  \
    grep -v GRANT | \
    grep -v TRIGGER | \
    grep -v DROP | \
    grep -v "CREATE INDEX" | \
    grep -v "ADD CONSTRAINT" | \
    grep -v "ALTER TABLE" | \
    grep -v "PRIMARY" | \
    sed 's/^.*geometry(Point.*$/    geopunt GEOMETRY(Point,28992)/' | \
    sed 's/igp_sw44z0001_cmg_owner\.//' | \
    psql -v ON_ERROR_STOP=1 -d handelsregister -h ${DATABASE_PORT_5432_TCP_ADDR} -U handelsregister
done

# PUT BAVK WD! ^*&^*^
cd /app/
