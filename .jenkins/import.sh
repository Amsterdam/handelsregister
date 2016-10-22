#!/bin/bash

set -e
set -u

DIR="$(dirname $0)"

dc() {
	docker-compose -p hr_import -f ${DIR}/docker-compose.yml $*;
}

trap 'dc kill ; dc rm -f' EXIT

rm -rf ${DIR}/backups
mkdir -p ${DIR}/backups

dc build --pull

dc up -d database

dc run --rm tests

# load latest bag into database
echo "load latest bag database"
dc exec -T database update-atlas.sh

echo "create hr api database"
# create the hr_data
dc run --rm importer

echo "create hr dump"
# run the backup shizzle
dc run --rm db-backup
