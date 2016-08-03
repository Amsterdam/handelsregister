"""
From the original dump
fill the stelselpedia dumps
"""

from datasets.kvkdump.models import KvkMaatschappelijkeActiviteit
from datasets.kvkdump.models import KvkPersoon
from datasets.kvkdump.models import KvkVestiging

from datasets.hr.models import Communicatiegegevens
from datasets.hr.models import Handelsnaam
from datasets.hr.models import MaatschappelijkeActiviteit
from datasets.hr.models import Persoon
from datasets.hr.models import Vestiging

from django.conf import settings

import logging

log = logging.getLogger(__name__)


class BatchImport(object):

    item_handle = None
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

    def process_rows(self):
        for job, endjob, start, end, total, qs in self.batch_qs():
            for item in qs:
                self.process_item(item)

    def process_item(self, item):
        """
        Handle a single item/row.
        """
        raise(NotImplementedError)


def load_mac_row(mac_object):
    m = mac_object

    for handelsnaam in m.handelsnamen.all():
        Handelsnaam.objects.create(
          macid=m.macid,
          handelsnaam=handelsnaam,
        )

    comms, created = Communicatiegegevens.objects.create(
        macid=m.macid,
        domeinnaam1=m.domeinnaam1,
        domeinnaam2=m.domeinnaam2,
        domeinnaam3=m.domeinnaam3,
        emailadres1=m.emailadres1,
        emailadres2=m.emailadres2,
        emailadres3=m.emailadres3,
        toegangscode1=m.toegangscode1,
        toegangscode2=m.toegangscode2,
        toegangscode3=m.toegangscode3,
        communicatienummer1=m.nummer1,
        communicatienummer2=m.nummer2,
        communicatienummer3=m.nummer3,
        soort1=m.soort1,
        soort2=m.soort2,
        soort3=m.soort3,
    )

    naam = '?'
    if m.handelsnamen.count() > 0:
        # Pick the first name
        naam = m.handelsnamen.all()[0].handelsnaam

    MaatschappelijkeActiviteit.objects.create(
        macid=m.macid,
        kvknummer=m.kvknummer,
        naam=naam,
        datum_aanvang=m.datumaanvang,
        datum_einde=m.datumeinde,
        non_mailing=((m.nonmailing or '').lower() == 'Ja'),
        totaal_werkzame_personen=m.totaalwerkzamepersonen,
        fulltime_werkzame_personen=m.fulltimewerkzamepersonen,
        parttime_werkzame_personen=m.parttimewerkzamepersonen,
        communicatiegegevens=comms,
    )


def load_ves_row(ves_object):
    v = ves_object
    Vestiging.objects.create(
        vesid=v.vesid,
        sbicode_hoofdactiviteit=v.sbicodehoofdactiviteit,
        sbicode_nevenactiviteit1=v.sbicodenevenactiviteit1,
        sbicode_nevenactiviteit2=v.sbicodenevenactiviteit2,
        sbicode_nevenactiviteit3=v.sbicodenevenactiviteit3,
        sbi_omschrijving_hoofdact=v.sbiomschrijvinghoofdact,
        sbi_omschrijving_nevenact1=v.sbiomschrijvingnevenact1,
        sbi_omschrijving_nevenact2=v.sbiomschrijvingnevenact2,
        sbi_omschrijving_nevenact3=v.sbiomschrijvingnevenact3,
    )


def load_prs_row(prs_object):
    p = prs_object
    Persoon.objects.create(
        prsid=p.prsid,
        rechtsvorm=p.rechtsvorm,
        uitgebreide_rechtsvorm=p.uitgebreiderechtsvorm,
        volledige_naam = p.volledigenaam,
    )


class MAC_batcher(BatchImport):

    queryset = KvkMaatschappelijkeActiviteit.objects.all().order_by('macid')

    def process_item(self, item):
        load_mac_row(item)


class VES_batcher(BatchImport):

    queryset = KvkVestiging.objects.all().order_by('vesid')

    def process_item(self, item):
        load_ves_row(item)


class PRS_batcher(BatchImport):

    queryset = KvkPersoon.objects.all().order_by('prsid')

    def process_item(self, item):
        load_prs_row(item)


def fill_stelselpedia():
    """
    Go through all tables and fill Stelselpedia tables.
    """
    MAC_batcher().process_rows()
    PRS_batcher().process_rows()
    VES_batcher().process_rows()
