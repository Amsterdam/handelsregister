#!/bin/bash

set -e
set -u

DIR="$(dirname $0)"

dc() {
	docker-compose -p hr -f ${DIR}/docker-compose_acc.yml $*;
}

trap 'dc kill ; dc rm -f' EXIT

rm -rf ${DIR}/backups
mkdir -p ${DIR}/backups

dc build --pull

dc up -d database

dc run --rm tests

# load latest bag into database
echo "load latest bag database"
dc exec -T database update-db.sh atlas

echo "create hr api database"
# create the hr_data
dc run --rm importer

espeak "Importing H R  DB is DONE!" || echo "DONE!"

echo "create hr dump"
# run the backup shizzle
dc run --rm db-backup

echo "create hr index"
dc up importer_el1 importer_el2 importer_el3

docker wait hr_importer_el1_1 hr_importer_el2_1 hr_importer_el3_1

dc run --rm el-backup

espeak "Creating H R index is DONE!" || echo "DONE!"
