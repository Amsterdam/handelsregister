# import sys

from django.core.management import BaseCommand

from datasets import build_hr_data
from datasets.hr import improve_location_with_search
from datasets.hr import models

import logging

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Import HR data from handel regster makelaarsuite (mks) dump

    clear data using:

    - manage.py migrate handelsregister zero

    apply new/updated migrations

    - manage.py migrate handelsregister

    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--bag',
            action='store_true',
            dest='bag',
            default=False,
            help='Fill hr_baggeo table')

        parser.add_argument(
            '--geovestigingen',
            action='store_true',
            dest='geo_vest',
            default=False,
            help='Fill hr_geovestigingen table')

        parser.add_argument(
            '--search',
            action='store_true',
            dest='searchapi',
            default=False,
            help='Fill hr_locatie with search api')

        parser.add_argument(
            '--clearsearch',
            action='store_true',
            dest='clearsearch',
            default=False,
            help='Clear hr_locate from search api results')

    def handle(self, *args, **options):
        """
        validate and execute import task
        """
        log.info('Handelsregister import started')

        if options['bag']:
            build_hr_data.fill_location_with_bag()
        elif options['geo_vest']:
            build_hr_data.fill_geo_table()
        elif options['searchapi']:
            improve_location_with_search.guess()
        elif options['clearsearch']:
            build_hr_data.clear_autocorrect()
        else:
            # convert mks dump
            build_hr_data.fill_stelselpedia()
            # now update mks locations with bag locations
            build_hr_data.fill_location_with_bag()
            assert models.GeoVestigingen.objects.count() > 200.000
