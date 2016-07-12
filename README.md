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

	(sudo) docker-compose start -d

or

	docker-compose up -d

The API should now be available on http://localhost:8100/nap


To run an import, execute:

Make sure your database is up to date

	./handelsregister/manage.py migrate

Import the data's

	./handelsregister/manage.py run_import


To see the various options for partial imports, execute:

	./handelsregister/manage.py run_import --help


To import the latest database from acceptance:

	docker exec -it $(docker-compose ps -q database) update-handelsregister.sh

To import the latest elastic index from acceptance:

	docker exec -it $(docker-compose ps -q elasticsearch) update-handelsregister.sh
