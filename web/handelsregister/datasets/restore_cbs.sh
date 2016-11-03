#!/usr/bin/env bash

set -u   # crash on missing env variables
set -e   # stop on any error

python ./manage.py loaddata ./datasets/kvkdump/fixture_files/hcat.json
python ./manage.py loaddata ./datasets/kvkdump/fixture_files/scat.json
python ./manage.py loaddata ./datasets/kvkdump/fixture_files/sbicodes.json
