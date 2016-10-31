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


Import the latest BAG geo data

    docker-compose exec database update-db.sh atlas

Load latest makelaarsuite data from the object store
create data folder and set the object store password

    python get_mks_dumps.py

Load the sql dump into the database

    ./loaddumps_local.sh

Copy geodata from atlas into handelsregister database
NOTE: do not put newlines in here

    ./copy_bagvbo_hr_local.sh

Now we are ready in create the Handelsregister (hr) databases
for the api and geoviews for mapserver

    ./handelsregister/manage.py run_import

To see the various options for imports, execute:

    ./handelsregister/manage.py run_import --help

To fix missing location geodata with the search api
for some locations we have only an adress

    ./handelsregister/manage.py run_import --search

Finally build the geodataview

    ./handelsregister/manage.py run_import --geovestigingen


Import Quickstart
-----------------
    Download a prepared database..

    docker-compose exec database update-db.sh handelsregister


The API should now be available on http://localhost:8100/handelsregister
