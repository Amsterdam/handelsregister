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

# load atlas / bag database

dc build --pull

dc up -d database

# load latest mks dump into database
dc run --rm importer_mks

# load latest bag into database
dc exec -T database update-atlas.sh

echo 'Copy bag geometrie naar hg_geobag'
dc run --rm bag_vbo_import

# create the hr_data
dc run --rm importer

# run the backup shizzle
dc run --rm db-backup
