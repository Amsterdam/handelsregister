#!/bin/bash

# This script loads the database dumps retrieved from Makelaarssuite (MKS) into
# a specific schema in a database. It is a parametrized adaptation of loaddumps.sh
# to make the database connection without touching the legacy scripts.

# the following steps are taken:
# 1) Retrieve the data from MKS and cache it in ./data (~200Mb) (get_mks_dumps.py)
# 2) Load the SQL data into Postgres (psql)
# 3) Create the Handelsregister tables (Django management command) 

# The following env vars need to be set:
# - PGPASSWORD or DATABASE_PW_lOCATION
# - HANDELSREGISTER_OBJECTSTORE_PASSWORD or HANDELSREGISTER_OBJECTSTORE_PW_LOCATION
# - POSTGIS_SCHEMA (the db-schema where postgis extension is installed)


set -e
set -u

python get_mks_dumps.py

for f in data/*.gz; do
    STEM=$(basename "${f}" .gz)
    gunzip -c "${f}" > unzipped/"${STEM}"
done

export PGPASSWORD=${PGPASSWORD-$(cat $DATABASE_PW_LOCATION)}
export HANDELSREGISTER_SCHEMA=${DATABASE_SCHEMA%%,*}

psql -d $DATABASE_NAME -h $DATABASE_HOST_OVERRIDE -U $DATABASE_USER -v search_path=$DATABASE_SCHEMA -c "\
DROP TABLE IF EXISTS $HANDELSREGISTER_SCHEMA.kvkvesm00;\
DROP TABLE IF EXISTS $HANDELSREGISTER_SCHEMA.kvkprsashm00;\
DROP TABLE IF EXISTS $HANDELSREGISTER_SCHEMA.kvkhdnm00;\
DROP TABLE IF EXISTS $HANDELSREGISTER_SCHEMA.kvkmacm00;\
DROP TABLE IF EXISTS $HANDELSREGISTER_SCHEMA.kvkkvkprsm00;\
DROP TABLE IF EXISTS $HANDELSREGISTER_SCHEMA.kvkveshdnm00;\
DROP TABLE IF EXISTS $HANDELSREGISTER_SCHEMA.kvkprsm00;\
DROP TABLE IF EXISTS $HANDELSREGISTER_SCHEMA.kvkprsashm00;\
DROP TABLE IF EXISTS $HANDELSREGISTER_SCHEMA.kvkveshism00;\
DROP TABLE IF EXISTS $HANDELSREGISTER_SCHEMA.kvkadrm00\
"

cd /app/unzipped/

# Load all sql files
# Ignore lines which match certain patterns (grep)
# or replace values with '' (sed)
for sql in *.sql; do
    grep -v OWNER $sql | grep -v search_path | grep -v REVOKE |  \
    grep -v ^GRANT | \
    grep -v "CREATE TRIGGER" | \
    grep -v ^DROP | \
    grep -v "CREATE INDEX" | \
    grep -v "ADD CONSTRAINT" | \
    grep -v "ALTER TABLE" | \
    grep -v "PRIMARY KEY (" | \
    sed "s/^.*geometry(Point.*$/    geopunt $POSTGIS_SCHEMA.geometry(Point,28992)/" | \
    sed -r "s/igp_[a-zA-Z0-9_]+_cmg_owner\./$HANDELSREGISTER_SCHEMA./" | \
    psql -v ON_ERROR_STOP=1 -v search_path=$DATABASE_SCHEMA -d $DATABASE_NAME -h $DATABASE_HOST_OVERRIDE -U $DATABASE_USER
done

# PUT BAVK WD! ^*&^*^
cd /app/

./manage.py run_import