"""
All commands to create a functioning HR api dataset
"""

import logging

from django.core.management import BaseCommand

from datasets import build_hr_data
from datasets import build_cbs_sbi
from datasets import build_ds_data
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
            '--bagfix',
            action='store_true',
            dest='bag',
            default=False,
            help='Fill hr_locatie with hr_baggeo table')

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

        parser.add_argument(
            '--cbs_sbi',
            action='store_true',
            dest='cbs_sbi',
            default=False,
            help='Fill cbs sbi-codes')

        parser.add_argument(
            '--dataselectie',
            action='store_true',
            dest='dataselectie',
            default=False,
            help='Fill dataselectie view')

    def bag_check(self):
        if models.GeoVBO.objects.count() < 10000:
            raise ValueError(
                'Import bag data with "copy_bagvbo_to_hr(local).sh"')

    def handle(self, *args, **options):
        """
        validate and execute import task
        """
        LOG.info('Handelsregister import started')

        if options['bag']:
            # load bag data in GeoVBO with
            # copy_bag_to_hr script
            self.bag_check()
            build_hr_data.fill_location_with_bag()
            location_stats.log_rapport_counts(action='bag')
        elif options['geo_vest']:
            build_hr_data.fill_geo_table()
            location_stats.log_rapport_counts(action='map')
        elif options['cbs_sbi']:
            build_cbs_sbi.cbsbi_table()
        elif options['dataselectie']:
            build_ds_data._build_joined_ds_table()
            # import cProfile
            # cProfile.runctx('build_ds_data._build_joined_ds_table()', globals(), locals(), '/tmp/statsds_data')
            location_stats.log_rapport_counts(action='ds')
        elif options['searchapi']:
            improve_location_with_search.guess()
            location_stats.log_rapport_counts(action='fix')
        elif options['clearsearch']:
            build_hr_data.clear_autocorrect()
        elif options['stats']:
            location_stats.log_rapport_counts()
        else:
            # convert mks dump
            self.bag_check()
            build_hr_data.fill_stelselpedia()
            location_stats.log_rapport_counts()
            location_stats.log_rapport_counts(action='mks')
            # now update mks locations with bag locations
            # check if bag data is correctly loaded
            # we need bag data to correct missing geometry data
            build_hr_data.fill_location_with_bag()
            LOG.info('hr_geovestigingen %s', models.Locatie.objects.count())
            assert models.GeoVestigingen.objects.count() == 0
            assert models.Locatie.objects.count() > 200000
            location_stats.log_rapport_counts(action='bag')
