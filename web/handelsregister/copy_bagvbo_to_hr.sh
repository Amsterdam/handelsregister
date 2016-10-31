#!/usr/bin/env bash

set -u
set -e

#chmod 0600 .pgpass
#
echo database:5432:handelsregister:handelsregister:insecure >> ~/.pgpass
echo database:5432:atlas:handelsregister:insecure >> ~/.pgpass
chmod 0600 ~/.pgpass

echo copying bag vbo geo -> hr_geovbo tabel

psql -U handelsregister -h database atlas -c \
        '\copy (SELECT v.id, v.landelijk_id, n.landelijk_id, geometrie from bag_verblijfsobject v, bag_nummeraanduiding n WHERE n.verblijfsobject_id = v.id AND n.hoofdadres) TO STDOUT' \
        | psql -U handelsregister -h database handelsregister -c \
                '\copy hr_geovbo (id, bag_vbid, bag_numid, geometrie) FROM STDIN'
