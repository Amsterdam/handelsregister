#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error
set -x

echo 'Downloading latest mks dumps'
# uses data and unzipped dir
python get_mks_dumps.py

echo 'Store mks dumps in database'
source loaddumps.sh
# to test locally
# source loaddumps_local.sh


# load mks data into HR models, complement with BAG information
python manage_gevent.py run_import

# import sbicodes
python manage_gevent.py run_import --cbs_sbi
# cleanup codes / ambiguity and make relation with activiteiten
python manage_gevent.py run_import --cbs_sbi_validate

# autocorrect locations fields with search resultaten
python manage_gevent.py run_import --search

# create geoviews
python manage_gevent.py run_import --geovestigingen

# create dataselectie
python manage_gevent.py run_import --dataselectie --partial=3/3 &
python manage_gevent.py run_import --dataselectie --partial=2/3 &
python manage_gevent.py run_import --dataselectie --partial=1/3 &

FAIL=0

for job in `jobs -p`
do
	echo $job
	wait $job || let "FAIL+=1"
done

echo $FAIL

if [ "$FAIL" == "0" ];
then
    echo "YAY!"
else
    echo "FAIL! ($FAIL)"
    echo 'Elastic Import Error. 1 or more workers failed'
    exit 1
fi


# validate that all tables contain values
# and enough counts
python manage_gevent.py run_import --validate_import
