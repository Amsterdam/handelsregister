Handelsregister API
=====================

Handelsregister (HR)

Serve a stelselpedia API of Handelsregister items

Data source is Makelaarssuite (mks)


Requirements
------------

* Docker-Compose (required)


Developing
----------

Use `docker-compose` to start a local database.

	docker-compose up -d

Manual
------

To run an complete import, execute:

Make sure your database is up to date

	./handelsregister/manage.py migrate


Import the atlas geo data

    docker-compose exec database update-atlas.sh

Load latest data from the object store
create data folder and set the object store password

    python load_mks_dumps.py

Copy geodata from atlas into handelsregister database
NOTE: do not put newlines in here

    psql -h 127.0.0.1 -p 5406 -U handelsregister atlas -c '\copy (SELECT id, landelijk_id, geometrie from bag_verblijfsobject) TO STDOUT' | psql -h 127.0.0.1 -p 5406 -U handelsregister handelsregister -c '\copy hr_geovbo (id, bag_vbid, geometrie) FROM STDIN'

Build data for the api and mapserver

	./handelsregister/manage.py run_import

To see the various options for partial imports, execute:

	./handelsregister/manage.py run_import --help


Import Quickstart
-----------------

    docker-compose exec database update-handelsregister.sh
    ./web/handelsregister/manage.py migrate hr zero
    ./web/handelsregister/manage.py migrate hr
    ./web/handelsregister/manage.py run_import


The API should now be available on http://localhost:8100/handelsregister
