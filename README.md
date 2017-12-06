Handelsregister API
=====================

Handelsregister (HR)

Serve a stelselpedia API of Handelsregister items

Data source is Makelaarssuite (mks) / cbs voor sbi codes


Requirements
------------

* Docker-Compose (required)


Developing
----------

Use `docker-compose` to start a local database, and latest codebase.

	docker-compose up -d --build

Quickstart Import
-----------------

Works only for amsterdam developers with published ssh keys.

    Download a prepared database..works only within 'gemeente Amsterdam network'

    docker-compose exec database update-db.sh handelsregister


Manual Import
-------------

The .jenkins-import folder contains the actual steps: here is a summary

Create a virtual python environement and install packages.

     pip install -r requirements.txt

To run an complete import, execute:


Make sure your database is up to date

      # this is automatic after previous docker-compose up -d  --build
      ./manage.py migrate

Import the latest BAG geo data

     docker-import-dev.sh

Load latest makelaarsuite data from the object store

Prerequisites: create data folder and set Objectstore passworfind d

	cd  web/handelsregister
	mkdir data
	export HANDELSREGISTER_OBJECTSTORE_PASSWORD=<password here>
        python get_mks_dumps.py

Load the sql dump into the database

    ./loaddumps_local.sh

Now we are ready in create the Handelsregister (hr) databases
for the api and geoviews for mapserver

     ./manage.py run_import

To see the various options for imports, execute:

     ./manage.py run_import --help

To load the csb sbi (activiteiten) data:

     ./manage.py run_import --cbs_sbi
     ./manage.py run_import --cbs_sbi_validate

To fix missing location geodata with the search api
for some locations we have only an adress

     ./manage.py run_import --search

Build the geodataview

     ./manage.py run_import --geovestigingen

Finally build the dataselectie view (if you need it....)

    ./manage.py run_import --dataselectie

SBI CODES
---------

to update the sbi code database:

	The nocache arguments makes sure we use the current 'CBS' api.

    python manage.py run_import cbs_sbi --nocache

    python manage.py run_import cbs_sbi


The API should now be available on http://localhost:8100/handelsregister
