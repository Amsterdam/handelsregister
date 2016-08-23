#!/bin/bash

set -e
set -u

DIR="$(dirname $0)"

dc() {
	docker-compose -f ${DIR}/docker-compose.yml $*;
}

trap 'dc kill ; dc rm -f' EXIT

rm -rf ${DIR}/backups
mkdir -p ${DIR}/backups

dc build --pull
# import new mks dump data in database
dc run --rm importer_mks
# create the hr_data
dc up importer
# wait until all building is done
import_status=`docker wait jenkins_importer_1`

# count the errors.
import_error=`echo $import_status | grep -o "1" | wc -l`

echo $import_error

if [ $import_error > 0 ]
then
    echo 'Import Error!! You SUCK!'
    exit -1
fi

# run the backup shizzle
dc run --rm db-backup
#dc run --rm el-backup

echo 'You are awesome and done! <3'
