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
# TEMPORARY VES filter on mac id 100000000012419559
for sql in *.sql; do
    grep -v OWNER $sql | grep -v search_path | grep -v REVOKE |  \
    grep -v ^GRANT | \
    grep -v "CREATE TRIGGER" | \
    grep -v ^DROP | \
    grep -v "CREATE INDEX" | \
    grep -v "ADD CONSTRAINT" | \
    grep -v "ALTER TABLE" | \
    grep -v "PRIMARY KEY (" | \
    grep -v 100000000012419606 | \
    grep -v 100000000012419529 | \
    grep -v 100000000012419505 | \
    grep -v 100000000012419495 | \
    grep -v 100000000012419575 | \
    grep -v 100000000012419612 | \
    grep -v 100000000012419586 | \
    grep -v 100000000012419477 | \
    grep -v 100000000012419523 | \
    grep -v 100000000012419559 | \
    grep -v 100000000012419483 | \
    grep -v 100000000012419565 | \
    grep -v 100000000012419592 | \
    grep -v 100000000012419553 | \
    grep -v 100000000012419535 | \
    grep -v 100000000012419547 | \
    grep -v 100000000012419511 | \
    grep -v 100000000012419517 | \
    grep -v 100000000012419471 | \
    grep -v 100000000012419489 | \
    grep -v 100000000012419541 | \
    grep -v 100000000012419465 | \
    sed 's/^.*geometry(Point.*$/    geopunt GEOMETRY(Point,28992)/' | \
    sed -r 's/igp_[a-zA-Z0-9_]+_cmg_owner\.//' | \
    psql -v ON_ERROR_STOP=1 -d handelsregister -h database -U handelsregister
done

# PUT BAVK WD! ^*&^*^
cd /app/
