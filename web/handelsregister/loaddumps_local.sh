#!/bin/bash

set -e
set -u
set -x

# set local env variables used by local dockers
export DATABASE_PORT_5432_TCP_ADDR=127.0.0.1
export DATABASE_PORT_5432_TCP_PORT=5406
export PGPASSWORD="insecure"

echo 'extracting latest kvk dump files'
for f in data/*.gz; do
    STEM=$(basename "${f}" .gz)
    gunzip -c "${f}" > unzipped/"${STEM}"
done

psql -d handelsregister -h ${DATABASE_PORT_5432_TCP_ADDR} -p ${DATABASE_PORT_5432_TCP_PORT} -U handelsregister -f dropallkvk.sql

cd unzipped/

# Load all sql files

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
    sed -r 's/igp_[a-zA-Z0-9_]+_cmg_owner\.//' | \
    psql -v ON_ERROR_STOP=1 -d handelsregister -h ${DATABASE_PORT_5432_TCP_ADDR} -p  ${DATABASE_PORT_5432_TCP_PORT} -U handelsregister
done

cd ..
