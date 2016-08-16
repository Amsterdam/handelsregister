"""
From the original dump
fill the stelselpedia dumps
"""
import datetime
import logging
import time
from decimal import Decimal
from typing import List

from django.conf import settings
from django.db import transaction

from datasets.hr.models import Communicatiegegevens, Onderneming, Locatie
from datasets.hr.models import Functievervulling
from datasets.hr.models import Handelsnaam
from datasets.hr.models import MaatschappelijkeActiviteit
from datasets.hr.models import Persoon
from datasets.hr.models import Vestiging
from datasets.kvkdump.models import KvkFunctievervulling, KvkAdres
from datasets.kvkdump.models import KvkMaatschappelijkeActiviteit
from datasets.kvkdump.models import KvkPersoon
from datasets.kvkdump.models import KvkVestiging

BAG_NUMMERAANDUIDING = "https://api.datapunt.amsterdam.nl/bag/nummeraanduiding/{}/"
BAG_VERBLIJFSOBJECT = "https://api.datapunt.amsterdam.nl/bag/verblijfsobject/{}/"

log = logging.getLogger(__name__)


class BatchImport(object):
    item_handle = None
    queryset = None
    batch_size = 4000

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

        log.info("STARTING BATCHER JOB: %s" % (self.__class__.__name__))
        log.info("PART: %s OF %s" % (numerator + 1, denominator))

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
            t_start = time.time()
            yield (i + 1, total_batches + 1, start, end, total, qs[start:end])
            log.info("CHUNK %5s - %-5s  in %.3f seconds" % (
                start, end, time.time() - t_start))

    def process_rows(self):
        for job, end_job, start, end, total, qs in self.batch_qs():
            with transaction.atomic():
                for item in qs:
                    self.process_item(item)

    def process_item(self, item):
        """
        Handle a single item/row.
        """
        raise NotImplementedError()


def _as_adres(a: KvkAdres) -> Locatie:
    loc = Locatie(
        id=str(a.adrid),
        volledig_adres=a.volledigadres,
        toevoeging_adres=a.toevoegingadres,
        afgeschermd=_parse_indicatie(a.afgeschermd),
        postbus_nummer=a.postbusnummer,
        straat_huisnummer=a.straathuisnummer,
        postcode_woonplaats=a.postcodewoonplaats,
        regio=a.regio,
        land=a.land,
        geometry=a.geopunt,
    )

    if a.identificatieaoa:
        loc.bag_nummeraanduiding = BAG_NUMMERAANDUIDING.format(a.identificatieaoa)

    if a.identificatietgo:
        loc.bag_adresseerbaar_object = BAG_VERBLIJFSOBJECT.format(a.identificatietgo)

    loc.save()
    return loc


def _as_communicatiegegevens(m: KvkMaatschappelijkeActiviteit) -> List[Communicatiegegevens]:
    cg1, cg2, cg3 = None, None, None
    if m.domeinnaam1 or m.emailadres1 or m.nummer1:
        cg1 = Communicatiegegevens(
            domeinnaam=m.domeinnaam1,
            emailadres=m.emailadres1,
            toegangscode=m.toegangscode1,
            communicatie_nummer=m.nummer1,
            soort_communicatie_nummer=m.soort1,
        )
    if m.domeinnaam2 or m.emailadres2 or m.nummer2:
        cg2 = Communicatiegegevens(
            domeinnaam=m.domeinnaam2,
            emailadres=m.emailadres2,
            toegangscode=m.toegangscode2,
            communicatie_nummer=m.nummer2,
            soort_communicatie_nummer=m.soort2,
        )
    if m.domeinnaam3 or m.emailadres3 or m.nummer3:
        cg3 = Communicatiegegevens(
            domeinnaam=m.domeinnaam3,
            emailadres=m.emailadres3,
            toegangscode=m.toegangscode3,
            communicatie_nummer=m.nummer3,
            soort_communicatie_nummer=m.soort3,
        )

    return [c for c in (cg1, cg2, cg3) if c]


def _parse_decimal_date(d: Decimal) -> datetime.date:
    if not d:
        return None

    return datetime.datetime.strptime(str(d), "%Y%m%d")


def _parse_indicatie(s: str) -> bool:
    return bool(s and s.lower() == 'ja')


def load_mac_row(mac_object: KvkMaatschappelijkeActiviteit):
    m = mac_object

    communicatiegegevens = _as_communicatiegegevens(m)
    for c in communicatiegegevens:
        c.save()

    mac = MaatschappelijkeActiviteit.objects.create(
        id=str(m.macid),
        kvk_nummer=m.kvknummer,
        naam=m.naam,
        datum_aanvang=_parse_decimal_date(m.datumaanvang),
        datum_einde=_parse_decimal_date(m.datumeinde),
        non_mailing=_parse_indicatie(m.nonmailing),
    )

    if _parse_indicatie(m.indicatieonderneming):
        ond = Onderneming.objects.create(
            id=str(m.macid),
            totaal_werkzame_personen=m.totaalwerkzamepersonen,
            fulltime_werkzame_personen=m.fulltimewerkzamepersonen,
            parttime_werkzame_personen=m.parttimewerkzamepersonen,
        )
        mac.onderneming = ond
        mac.save()

        for hn in m.handelsnamen.all():
            Handelsnaam.objects.create(
                id=hn.hdnid,
                handelsnaam=hn.handelsnaam,
                onderneming=ond,
            )

    for kvk_adres in m.adressen.all():
        if kvk_adres.typering == 'bezoekLocatie':
            mac.bezoekadres = _as_adres(kvk_adres)

        if kvk_adres.typering == 'postLocatie':
            mac.postadres = _as_adres(kvk_adres)

    mac.communicatiegegevens.add(*communicatiegegevens)
    return mac


def load_ves_row(ves_object):
    v = ves_object
    Vestiging.objects.create(
        vesid=v.vesid,
        vestigingsnummer=v.vestigingsnummer,
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
        volledige_naam=p.volledigenaam,
    )


def load_functievervulling_row(functievervulling_object):
    f = functievervulling_object
    Functievervulling.objects.create(
        fvvid=f.ashid,
        functietitel=f.functie
    )


class MACbatcher(BatchImport):
    queryset = (KvkMaatschappelijkeActiviteit.objects
                .prefetch_related('handelsnamen', 'adressen')
                .order_by('macid'))

    def process_item(self, item):
        load_mac_row(item)


class VESbatcher(BatchImport):
    queryset = KvkVestiging.objects.order_by('vesid')

    def process_item(self, item):
        load_ves_row(item)


class PRSbatcher(BatchImport):
    queryset = KvkPersoon.objects.order_by('prsid')

    def process_item(self, item):
        load_prs_row(item)


class FunctievervullingBatcher(BatchImport):
    queryset = KvkFunctievervulling.objects.all().order_by('ashid')

    def process_item(self, item):
        load_functievervulling_row(item)


def fill_stelselpedia():
    """
    Go through all tables and fill Stelselpedia tables.
    """
    MACbatcher().process_rows()
    PRSbatcher().process_rows()
    VESbatcher().process_rows()
    FunctievervullingBatcher().process_rows()
