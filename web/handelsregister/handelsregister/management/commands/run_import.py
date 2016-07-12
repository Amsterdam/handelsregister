# import sys

from django.core.management import BaseCommand

from datasets import build_hr_data

import logging

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Import HR data from handel regster dump

    clear data using:

    - manage.py migrate bbga_data zero

    apply new/updated migrations

    - manage.py migrate bbga_data

    """

    # def add_arguments(self, parser):

    #    parser.add_argument(
    #        'csv_source',
    #        nargs=1,
    #        type=str,
    #        help='CSV bron bestand')

    def handle(self, *args, **options):
        """
        validate and execute import task
        """
        log.info('debug')
        build_hr_data.fill_stelselpedia()
