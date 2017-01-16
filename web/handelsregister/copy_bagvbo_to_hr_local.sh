#!/usr/bin/env bash

set -u
set -e

echo copying bag vbo geo hr_geovbo tabel

export PGPASSWORD="insecure"

psql -d atlas -h 127.0.0.1 -p  5406 -U handelsregister -c \
	'\copy (SELECT v.id, v.landelijk_id, n.landelijk_id, geometrie from bag_verblijfsobject v, bag_nummeraanduiding n WHERE n.verblijfsobject_id = v.id AND n.hoofdadres) TO STDOUT' \
| psql -d handelsregister -h 127.0.0.1 -p 5406 -U handelsregister -c \
	'\copy hr_geovbo (id, bag_vbid, bag_numid, geometrie) FROM STDIN'
