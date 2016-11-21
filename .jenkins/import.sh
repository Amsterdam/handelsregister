#!/bin/bash

set -e
set -u

DIR="$(dirname $0)"

dc() {
	docker-compose -p hr -f ${DIR}/docker-compose.yml $*;
}

trap 'dc kill ; dc rm -f' EXIT

echo "Do we have OS password?"
echo $OS_PASSWORD

rm -rf ${DIR}/backups
mkdir -p ${DIR}/backups

dc build --pull

dc up -d database

dc run --rm tests

# load latest bag into database
echo "load latest bag database"
dc exec -T database update-db.sh atlas

echo "create hr api database / reset elastic index"
# create the hr_data and reset elastic
dc run --rm importer

echo "DONE! importing mks into database"

echo "create hr dump"
# run the backup shizzle
dc run --rm db-backup

echo "create hr index"
dc up importer_el1 importer_el2 importer_el3

docker wait hr_importer_el1_1 hr_importer_el2_1 hr_importer_el3_1

dc run --rm el-backup

echo "DONE! with everything!"
