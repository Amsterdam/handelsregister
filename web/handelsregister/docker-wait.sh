#!/usr/bin/env bash

set -u
set -e
set -x


# wait for elastic
while ! nc -z elasticsearch 9200
do
 	echo "Waiting for elastic..."
 	sleep 0.5
done


# wait for postgres
while ! nc -z database 5432
do
	echo "Waiting for postgres..."
	sleep 0.5
done
