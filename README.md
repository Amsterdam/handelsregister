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

Use `docker-compose` to start a local database, and latest codebase.

	docker-compose up -d --build

Manual Import
-------------

To run an complete import, execute:

Make sure your database is up to date

	# this is automatic after previous docker-compose up -d  --build
	docker-compose exec database ./manage.py migrate

Import the latest BAG geo data

    docker-compose exec database update-db.sh atlas

Load latest makelaarsuite data from the object store

Prerequisites: create data folder and set Objectstore password

	cd  web/handelsregister
	mkdir data
	export HANDELSREGISTER_OBJECTSTORE_PASSWORD=<password here>
    python get_mks_dumps.py

Load the sql dump into the database

    ./loaddumps_local.sh

Copy geodata from atlas into handelsregister database
NOTE: do not put newlines in here

    ./copy_bagvbo_to_hr_local.sh

Now we are ready in create the Handelsregister (hr) databases
for the api and geoviews for mapserver

	# change back to the root of the project
	cd  ../..
    docker-compose exec database ./manage.py run_import

To see the various options for imports, execute:

    docker-compose exec database ./manage.py run_import --help

To fix missing location geodata with the search api
for some locations we have only an adress

    docker-compose exec database ./manage.py run_import --search

Build the geodataview

    docker-compose exec database ./manage.py run_import --geovestigingen

Finally build the dataselectie view (if you need it....)

    docker-compose exec database ./manage.py run_import --dataselectie


Quickstart Import
-----------------
    Download a prepared database..

    docker-compose exec database update-db.sh handelsregister 
    

The API should now be available on http://localhost:8100/handelsregister
