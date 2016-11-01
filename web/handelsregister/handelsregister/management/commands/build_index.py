# import sys

import time

from django.core.management import BaseCommand
from django.conf import settings

from search import build_index

import logging

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Index HR data from Handelsregster
    """
    ordered = ['mac', 'ves']

    index_tasks = {
        'mac': [build_index.index_mac_docs],
        'ves': [build_index.index_ves_docs],
    }

    delete_tasks = {
        'mac': [build_index.delete_hr_docs],
        'ves': [],
    }

    def add_arguments(self, parser):

        parser.add_argument(
            'dataset',
            nargs='*',
            default=self.ordered,
            help="Dataset to use, choose from {}".format(
                ', '.join(self.index_tasks.keys())))

        parser.add_argument(
            '--build',
            action='store_true',
            dest='build_index',
            default=False,
            help='Build elastic index from postgres')

        parser.add_argument(
            '--delete',
            action='store_true',
            dest='delete_indexes',
            default=False,
            help='Delete elastic indexes from elastic')

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

    def determine_datasets(self, options):
        """
        Determine
        """
        dataset = options['dataset']

        for ds in dataset:
            if ds not in self.index_tasks.keys():
                self.stderr.write("Unkown dataset: {}".format(ds))
                return

        sets = [ds for ds in self.ordered if ds in dataset]     # enforce order

        self.stdout.write("Working on {}".format(", ".join(sets)))

        return sets

    def handle(self, *args, **options):
        """
        validate and execute import task
        """
        log.info('Handelsregister import started')
        start = time.time()

        sets = self.determine_datasets(options)

        self.set_partial_config(options)

        for ds in sets:

            if options['build_index']:
                for task in self.index_tasks[ds]:
                    task()

            if options['delete_indexes']:
                for task in self.delete_tasks[ds]:
                    task()

        self.stdout.write(
            "Total Duration: %.2f seconds" % (time.time() - start))
