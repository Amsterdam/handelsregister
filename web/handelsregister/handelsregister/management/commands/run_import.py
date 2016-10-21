"""
All commands to create a functioning HR api dataset
"""

import logging

from django.core.management import BaseCommand

from datasets import build_hr_data
from datasets.hr import improve_location_with_search
from datasets.hr import models
from datasets.hr import location_stats


LOG = logging.getLogger(__name__)


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

        parser.add_argument(
            '--status',
            action='store_true',
            dest='stats',
            default=False,
            help='print location stats')

    def handle(self, *args, **options):
        """
        validate and execute import task
        """
        LOG.info('Handelsregister import started')

        if options['bag']:
            build_hr_data.fill_location_with_bag()
        elif options['geo_vest']:
            build_hr_data.fill_geo_table()
        elif options['searchapi']:
            ves_counts = location_stats.vestiging_stats()
            before = ves_counts[-1]
            improve_location_with_search.guess()
            ves_counts2 = location_stats.vestiging_stats()
            after = ves_counts2[-1]
            LOG.debug("Missing Before %s After %s", before, after)
        elif options['clearsearch']:
            build_hr_data.clear_autocorrect()
        elif options['stats']:
            location_stats.location_stats()
            location_stats.vestiging_stats()
            location_stats.mac_stats()
        else:
            # convert mks dump
            build_hr_data.fill_stelselpedia()
            # now update mks locations with bag locations
            # check if bag data is correctly loaded
            # we need bag data to correct missing geometry data
            assert models.GeoVBO.objects.count() > 10000
            build_hr_data.fill_location_with_bag()
            LOG.info('hr_geovestigingen %s', models.Locatie.objects.count())
            assert models.GeoVestigingen.objects.count() == 0
            assert models.Locatie.objects.count() > 200000
