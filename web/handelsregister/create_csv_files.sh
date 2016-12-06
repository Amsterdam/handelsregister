#!/usr/bin/env bash

set -u
set -e


echo 127.0.0.1:5406:handelsregister:handelsregister:insecure > .pgpass
echo 127.0.0.1:5406:atlas:handelsregister:insecure >> .pgpass

chmod 0600 .pgpass


psql -U handelsregister -h '127.0.0.1' -p 5406 handelsregister -c \
    "\copy (SELECT l.id, l.volledig_adres from hr_locatie l WHERE l.geometrie is null AND NOT l.volledig_adres LIKE 'Postbus%' ORDER BY l.volledig_adres) TO alles_onbekend.csv WITH CSV DELIMITER ';';" \

psql -U handelsregister -h '127.0.0.1' -p 5406 handelsregister -c \
    "\copy (SELECT bezoekadres_id, volledig_adres from hr_locatie, hr_vestiging WHERE bezoekadres_id = hr_locatie.id AND correctie = false ORDER BY volledig_adres) TO bezoek_onbekend.csv WITH CSV DELIMITER ';';" \

psql -U handelsregister -h '127.0.0.1' -p 5406 handelsregister -c \
    "\copy (SELECT bezoekadres_id, volledig_adres from hr_locatie, hr_vestiging WHERE bezoekadres_id = hr_locatie.id AND correctie = false ORDER BY volledig_adres) TO bezoek_onbekend.csv WITH CSV DELIMITER ';';" \


psql -U handelsregister -h '127.0.0.1' -p 5406 handelsregister -c \
    "\copy (SELECT bezoekadres_id, volledig_adres from hr_vestiging, hr_locatie WHERE bezoekadres_id = hr_locatie.id AND geometrie is null ORDER BY volledig_adres) TO geo_bezoek_onbekend_true.csv WITH CSV DELIMITER ';';" \





psql -U handelsregister -h '127.0.0.1' -p 5406 handelsregister -c \
    "\copy (SELECT l.id, l.volledig_adres, l.bag_vbid, l.query_string from hr_locatie l WHERE l.correctie = true ORDER BY l.volledig_adres) TO auto_fixed.csv WITH CSV DELIMITER ';';" \

