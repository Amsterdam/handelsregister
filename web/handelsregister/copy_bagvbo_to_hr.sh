#!/usr/bin/env bash

set -u
set -e

echo copying bag vbo geo hr_geovbo tabel

PGPASSWORD=insecure

psql -d atlas -h ${DATABASE_PORT_5432_TCP_ADDR} -p  ${DATABASE_PORT_5432_TCP_PORT} -U handelsregister -c \
	'\copy (SELECT v.id, v.landelijk_id, n.landelijk_id, geometrie from bag_verblijfsobject v, bag_nummeraanduiding n WHERE n.verblijfsobject_id = v.id AND n.hoofdadres) TO STDOUT' \
| psql -d handelsregister -h ${DATABASE_PORT_5432_TCP_ADDR} -p  ${DATABASE_PORT_5432_TCP_PORT} -U handelsregister -c \
	'\copy hr_geovbo (id, bag_vbid, bag_numid, geometrie) FROM STDIN'
