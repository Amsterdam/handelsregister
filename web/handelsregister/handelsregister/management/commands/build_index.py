# import sys

from django.core.management import BaseCommand
from django.conf import settings

from datasets import build_elk_index

import logging

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Index HR data from Handelsregster
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--partial',
            action='store',
            dest='partial_index',
            default=0,
            help='Build X/Y parts 1/3, 2/3, 3/3 1/1000')

    def set_partial_config(self, options):
        """
        Do partial configuration
        """
        if options['partial_index']:
            numerator, denominator = options['partial_index'].split('/')

            numerator = int(numerator) - 1
            denominator = int(denominator)

            assert(numerator <= denominator)

            settings.PARTIAL_IMPORT['numerator'] = numerator
            settings.PARTIAL_IMPORT['denominator'] = denominator

    def handle(self, *args, **options):
        """
        validate and execute import task
        """
        log.info('Handelsregister import started')

        self.set_partial_config(options)

        build_elk_index.index_mac_docs()
