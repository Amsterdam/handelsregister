#!/bin/bash

set -e
set -u

# wait for database to load
source docker-wait.sh

echo 'unzipping latest kvk dump files'

unzip $(ls -Art data/*.zip | tail -n 1) -d /app/unzipped/

psql -d handelsregister -h ${DATABASE_PORT_5432_TCP_ADDR} -U handelsregister -f dropallkvk.sql

cd /app/unzipped/

#Load all sql files

for sql in *.sql; do
    # Exclude duplicate sql.
    if [ "$sql" = "kvkadr.sql" ]
    then
        continue
    fi
    grep -v OWNER $sql | grep -v search_path | grep -v REVOKE |  \
    grep -v GRANT | \
    grep -v TRIGGER | \
    psql -v ON_ERROR_STOP=1 -d handelsregister -h ${DATABASE_PORT_5432_TCP_ADDR} -U handelsregister
done
