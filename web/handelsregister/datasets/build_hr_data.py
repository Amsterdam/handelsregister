"""
From the original dump

fill the stelselpedia dumps
"""

from datasets.kvkdump.models import Kvk_maatschappelijkeactiviteit
from datasets.kvkdump.models import Kvk_vestiging
from datasets.kvkdump import models as kvk_models

from datasets.hr_stelselpedia.models import MaatschappelijkeActiviteit
from datasets.hr_stelselpedia.models import Vestiging

from django.conf import settings

import logging

log = logging.getLogger(__name__)


class BatchImport(object):

    queryset = None
    batch_size = 10000

    def batch_qs(self):
        """
        Returns a (start, end, total, queryset) tuple
        for each batch in the given queryset.

        Usage:
            # Make sure to order your querset!
            article_qs = Article.objects.order_by('id')
            for start, end, total, qs in batch_qs(article_qs):
                print "Now processing %s - %s of %s" % (start + 1, end, total)
                for article in qs:
                    print article.body
        """
        qs = self.queryset

        batch_size = self.batch_size

        numerator = settings.PARTIAL_IMPORT['numerator']
        denominator = settings.PARTIAL_IMPORT['denominator']

        log.info("PART: %s OF %s" % (numerator+1, denominator))

        end_part = count = total = qs.count()
        chunk_size = batch_size

        start_index = 0

        # Do partial import
        if denominator > 1:
            chunk_size = int(total / denominator)
            start_index = numerator * chunk_size
            end_part = (numerator + 1) * chunk_size
            total = end_part - start_index

        log.info("START: %s END %s COUNT: %s CHUNK %s TOTAL_COUNT: %s" % (
            start_index, end_part, chunk_size, batch_size, count))

        # total batches in this (partial) bacth job
        total_batches = int(chunk_size / batch_size)

        for i, start in enumerate(range(start_index, end_part, batch_size)):
            end = min(start + batch_size, end_part)
            yield (i+1, total_batches+1, start, end, total, qs[start:end])


class MAC_batcher(BatchImport):

    queryset = Kvk_maatschappelijkeactiviteit.objects.all().order_by('macid')


class VES_batcher(BatchImport):

    queryset = Kvk_vestiging.objects.all().order_by('vesid')


def fill_stelselpedia():
    """
    For go through all tables and fill stelselpedia tables
    """
    # Go throuhgs all macs
    mks_mac_to_maatschappelijke_activiteit()

    # Go through vestigingen..

    # Go through...ect ect


def load_mac_row(mac_object):
    """
    Convert mac row to stelselpedia MAC
    """
    m = mac_object

    naam = '?'
    if m.handelsnamen.count() > 0:
        # Pick the first name
        naam = m.handelsnamen.all()[0].handelsnaam,

    MaatschappelijkeActiviteit.objects.update_or_create(
        macid=m.macid,
        kvknummer=m.kvknummer,
        naam=naam,
        datumaanvang=m.datumaanvang,
        datumeinde=m.datumeinde,
    )

    # create search document?


def mks_mac_to_maatschappelijke_activiteit():
    """
    Chunck loading of data in parts
    """

    mac_batcher = MAC_batcher()

    for job, endjob, start, end, total, qs in mac_batcher.batch_qs():
        for mac_item in qs:
            load_mac_row(mac_item)
