#!/usr/bin/env bash

set -u
set -e


# wait for elastic
while ! nc -z ${ELASTICSEARCH_PORT_9200_TCP_ADDR} ${ELASTICSEARCH_PORT_9200_TCP_PORT}
do
 	echo "Waiting for elastic..."
 	sleep 0.5
done


# wait for postgres
while ! nc -z ${DATABASE_PORT_5432_TCP_ADDR} ${DATABASE_PORT_5432_TCP_PORT}
do
	echo "Waiting for postgres..."
	sleep 0.5
done
