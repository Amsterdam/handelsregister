"""
From the original dump
fill the stelselpedia dumps
"""
import datetime
import logging
import time
from decimal import Decimal
from typing import List, Union

from django import db
from django.conf import settings
from django.db import transaction

from datasets.hr.models import Communicatiegegevens, Locatie, CommercieleVestiging, \
    NietCommercieleVestiging, Activiteit
from datasets.hr.models import Functievervulling
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
    with db.connection.cursor() as cursor:
        log.info("Converteren locaties")
        _converteer_locaties(cursor)

        log.info("Converteren onderneming")
        _converteer_onderneming(cursor)

        log.info("Converteren maatschappelijke activiteit")
        _converteer_maatschappelijke_activiteit(cursor)

        log.info("Converteren handelsnaam")
        _converteer_handelsnaam(cursor)

        for i in (1, 2, 3):
            log.info("Converteren MAC communicatie-gegevens-{0}".format(i))
            _converteer_mac_communicatiegegevens(cursor, i)

        log.info("Converteren commerciële vestiging")
        _converteer_commerciele_vestiging(cursor)

        log.info("Converteren niet-commerciële vestiging")
        _converteer_niet_commerciele_vestiging(cursor)

        log.info("Converteren vestiging")
        _converteer_vestiging(cursor)

        for i in (1, 2, 3):
            log.info("Converteren VES communicatie-gegevens-{0}".format(i))
            _converteer_ves_communicatiegegevens(cursor, i)

            # MACbatcher().process_rows()
            # PRSbatcher().process_rows()
            # VESbatcher().process_rows()
            # FunctievervullingBatcher().process_rows()

        log.info("Converteren hoofdactiviteit")
        _converteer_hoofdactiviteit(cursor)
        for i in (1, 2, 3):
            log.info("Converteren nevenactiviteit-{0}".format(i))
            _converteer_nevenactiviteit(cursor, i)

        log.info("Converteren handelsnaam vestiging")
        _converteer_handelsnaam_ves(cursor)

def _converteer_locaties(cursor):
    cursor.execute("""
INSERT INTO hr_locatie (
  id,
  volledig_adres,
  toevoeging_adres,
  afgeschermd,
  postbus_nummer,
  bag_nummeraanduiding,
  bag_adresseerbaar_object,
  straat_huisnummer,
  postcode_woonplaats,
  regio,
  land,
  geometry
)
    SELECT
      adrid,
      volledigadres,
      toevoegingadres,
      CASE afgeschermd
        WHEN 'Ja' THEN TRUE
        ELSE FALSE
      END,
      postbusnummer,
      'https://api.datapunt.amsterdam.nl/bag/nummeraanduiding/' || identificatieaoa || '/',
      'https://api.datapunt.amsterdam.nl/bag/verblijfsobject/' || identificatietgo || '/',
      straathuisnummer,
      postcodewoonplaats,
      regio,
      land,
      geopunt
    FROM kvkadrm00
        """)


def _converteer_onderneming(cursor):
    cursor.execute("""
INSERT INTO hr_onderneming (
  id,
  totaal_werkzame_personen,
  fulltime_werkzame_personen,
  parttime_werkzame_personen
)
  SELECT
    macid,
    totaalwerkzamepersonen,
    fulltimewerkzamepersonen,
    parttimewerkzamepersonen
  FROM kvkmacm00
  WHERE indicatieonderneming = 'Ja'
        """)


def _converteer_maatschappelijke_activiteit(cursor):
    cursor.execute("""
INSERT INTO hr_maatschappelijkeactiviteit (
  id,
  naam,
  kvk_nummer,
  datum_aanvang,
  datum_einde,
  incidenteel_uitlenen_arbeidskrachten,
  non_mailing,
  onderneming_id,
  postadres_id,
  bezoekadres_id
  --   eigenaar_id, hoofdvestiging_id
)
  SELECT
    m.macid,
    m.naam,
    m.kvknummer,
    to_date(to_char(m.datumaanvang, '99999999'), 'YYYYMMDD'),
    to_date(to_char(m.datumeinde, '99999999'), 'YYYYMMDD'),
    NULL,
    CASE m.nonmailing
    WHEN 'Ja'
      THEN TRUE
    WHEN 'Nee'
      THEN FALSE
    ELSE NULL
    END,
    CASE m.indicatieonderneming
    WHEN 'Ja'
      THEN m.macid
    ELSE NULL
    END,
    p.adrid,
    b.adrid
  FROM kvkmacm00 m
    LEFT JOIN kvkadrm00 p ON p.macid = m.macid AND p.typering = 'postLocatie'
    LEFT JOIN kvkadrm00 b ON b.macid = m.macid AND b.typering = 'bezoekLocatie'
        """)


def _converteer_handelsnaam(cursor):
    cursor.execute("""
INSERT INTO hr_handelsnaam (id, handelsnaam)
  SELECT
    hdnid,
    handelsnaam
  FROM kvkhdnm00
        """)

    cursor.execute("""
INSERT INTO hr_onderneming_handelsnamen(onderneming_id, handelsnaam_id)
  SELECT
    macid,
    hdnid
  FROM kvkhdnm00
    """)


def _converteer_handelsnaam_ves(cursor):
    cursor.execute("""
INSERT INTO hr_vestiging_handelsnamen(vestiging_id, handelsnaam_id)
  SELECT
    vesid,
    veshdnid
  FROM kvkveshdnm00
    """)

def _converteer_mac_communicatiegegevens(cursor, i):
    __converteer_any_communicatiegegevens(cursor, i, 'macid', 'kvkmacm00', 'maatschappelijkeactiviteit')


def _converteer_ves_communicatiegegevens(cursor, i):
    __converteer_any_communicatiegegevens(cursor, i, 'vesid', 'kvkvesm00', 'vestiging')


def __converteer_any_communicatiegegevens(cursor, i, id_col, source, target):
    cursor.execute("""
INSERT INTO hr_communicatiegegevens (
  id,
  domeinnaam,
  emailadres,
  toegangscode,
  communicatie_nummer,
  soort_communicatie_nummer
)
  SELECT
    {id_col} || '{index}',
    domeinnaam{index},
    emailadres{index},
    toegangscode{index},
    nummer{index},
    soort{index}
  FROM {source}
  WHERE domeinnaam{index} IS NOT NULL
        OR emailadres{index} IS NOT NULL
        OR toegangscode{index} IS NOT NULL
        OR nummer{index} IS NOT NULL
        OR soort{index} IS NOT NULL
            """.format(id_col=id_col, source=source, index=i))
    cursor.execute("""
INSERT INTO hr_{target}_communicatiegegevens (
  {target}_id,
  communicatiegegevens_id
)
  SELECT
    {id_col},
    {id_col} || '{index}'
  FROM {source}
  WHERE domeinnaam{index} IS NOT NULL
        OR emailadres{index} IS NOT NULL
        OR toegangscode{index} IS NOT NULL
        OR nummer{index} IS NOT NULL
        OR soort{index} IS NOT NULL
            """.format(id_col=id_col, source=source, target=target, index=i))


def _converteer_commerciele_vestiging(cursor):
    cursor.execute("""
INSERT INTO hr_commercielevestiging (
  id,
  totaal_werkzame_personen,
  fulltime_werkzame_personen,
  parttime_werkzame_personen,
  import_activiteit,
  export_activiteit
)
  SELECT
    vesid,
    totaalwerkzamepersonen,
    fulltimewerkzamepersonen,
    parttimewerkzamepersonen,
    CASE importactiviteit
    WHEN 'Ja'
      THEN TRUE
    WHEN 'Nee'
      THEN FALSE
    ELSE NULL END,
    CASE exportactiviteit
    WHEN 'Ja'
      THEN TRUE
    WHEN 'Nee'
      THEN FALSE
    ELSE NULL END
  FROM kvkvesm00
  WHERE typeringvestiging = 'CVS'
      """)


def _converteer_niet_commerciele_vestiging(cursor):
    cursor.execute("""
INSERT INTO hr_nietcommercielevestiging (
  id,
  ook_genoemd,
  verkorte_naam
)
  SELECT
    vesid,
    ookgenoemd,
    verkortenaam
  FROM kvkvesm00
  WHERE typeringvestiging = 'NCV'
      """)


def _converteer_vestiging(cursor):
    cursor.execute("""
INSERT INTO hr_vestiging
(
  id,
  vestigingsnummer,
  hoofdvestiging,
  naam,
  datum_aanvang,
  datum_einde,
  datum_voortzetting,
  maatschappelijke_activiteit_id,
  commerciele_vestiging_id,
  niet_commerciele_vestiging_id,
  bezoekadres_id,
  postadres_id
)

  SELECT
    v.vesid,
    v.vestigingsnummer,
    CASE v.indicatiehoofdvestiging
    WHEN 'Ja'
      THEN TRUE
    ELSE FALSE
    END,

    coalesce(v.naam, v.eerstehandelsnaam),
    to_date(to_char(v.datumaanvang, '99999999'), 'YYYYMMDD'),
    to_date(to_char(v.datumeinde, '99999999'), 'YYYYMMDD'),
    NULL,

    v.macid,
    CASE v.typeringvestiging
    WHEN 'CVS'
      THEN v.vesid
    ELSE NULL END,
    CASE v.typeringvestiging
    WHEN 'NCV'
      THEN v.vesid
    ELSE NULL END,
    b.adrid,
    p.adrid
  FROM kvkvesm00 v
    LEFT JOIN kvkadrm00 p ON p.vesid = v.vesid AND p.typering = 'postLocatie'
    LEFT JOIN kvkadrm00 b ON b.vesid = v.vesid AND b.typering = 'bezoekLocatie'
        """)


def _converteer_hoofdactiviteit(cursor):
    cursor.execute("""
INSERT INTO hr_activiteit (
  id,
  activiteitsomschrijving,
  sbi_code,
  sbi_omschrijving,
  hoofdactiviteit
)
  SELECT
    vesid || '0',
    omschrijvingactiviteit,
    CASE sbicodehoofdactiviteit
    WHEN '900302' THEN '9003'
    WHEN '889922' THEN '88992'
    WHEN '620202' THEN '6202'
    ELSE sbicodehoofdactiviteit END ,
    sbiomschrijvinghoofdact,
    TRUE
  FROM kvkvesm00
  WHERE sbicodehoofdactiviteit IS NOT NULL
    """)
    cursor.execute("""
INSERT INTO hr_vestiging_activiteiten (
  vestiging_id,
  activiteit_id
)
  SELECT
    vesid,
    vesid || '0'
  FROM kvkvesm00
  WHERE sbicodehoofdactiviteit IS NOT NULL
    """)


def _converteer_nevenactiviteit(cursor, i):
    cursor.execute("""
INSERT INTO hr_activiteit (
  id,
  sbi_code,
  sbi_omschrijving,
  hoofdactiviteit
)
  SELECT
    vesid || '{index}',
    CASE sbicodenevenactiviteit{index}
    WHEN '900302' THEN '9003'
    WHEN '889922' THEN '88992'
    WHEN '620202' THEN '6202'
    ELSE sbicodenevenactiviteit{index} END ,
    sbiomschrijvingnevenact{index},
    FALSE
  FROM kvkvesm00
  WHERE sbicodenevenactiviteit{index} IS NOT NULL
    """.format(index=i))

    cursor.execute("""
INSERT INTO hr_vestiging_activiteiten (
  vestiging_id,
  activiteit_id
)
  SELECT
    vesid,
    vesid || '{index}'
  FROM kvkvesm00
  WHERE sbicodenevenactiviteit{index}  IS NOT NULL
    """.format(index=i))