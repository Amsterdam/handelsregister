"""
From the original dump
fill the stelselpedia dumps
"""
import logging

from django import db
from django.conf import settings

from datasets.sbicodes.models import SBICodeHierarchy

from datasets.hr.models import Locatie
from datasets.hr.models import Onderneming
from datasets.hr.models import GeoVestigingen
from datasets.hr.models import Vestiging

log = logging.getLogger(__name__)


def fill_stelselpedia(keep_outside_amsterdam=False):
    """
    Go through all tables and fill Stelselpedia tables.
    """
    with db.connection.cursor() as cursor:
        sql_steps(
            cursor, keep_outside_amsterdam=keep_outside_amsterdam)


def sql_steps(cursor, keep_outside_amsterdam=False):

    log.info("Converteren locaties")
    _converteer_locaties(cursor)

    log.info("Converteren onderneming")
    _converteer_onderneming(cursor)

    log.info("Converteren maatschappelijke activiteit")
    _converteer_maatschappelijke_activiteit(cursor)

    log.info("Converteren handelsnaam")
    _converteer_handelsnaam(cursor)

    for i in (1, 2, 3):
        log.info("Converteren MAC communicatie-gegevens-%s", i)
        _converteer_mac_communicatiegegevens(cursor, i)

    log.info("Converteren commerciële vestiging")
    _converteer_commerciele_vestiging(cursor)

    log.info("Converteren niet-commerciële vestiging")
    _converteer_niet_commerciele_vestiging(cursor)

    log.info("Converteren vestiging")

    _converteer_vestiging(cursor)

    for i in (1, 2, 3):
        log.info("Converteren VES communicatie-gegevens-%s", i)
        _converteer_ves_communicatiegegevens(cursor, i)

    log.info("Converteren hoofdactiviteit")
    _converteer_hoofdactiviteit(cursor)
    for i in (1, 2, 3):
        log.info("Converteren nevenactiviteit-%s", i)
        _converteer_nevenactiviteit(cursor, i)

    log.info("Converteren handelsnaam vestiging")
    _converteer_handelsnaam_ves(cursor)

    log.info("Converteren hoofdvestiging")
    _converteer_hoofdvestiging(cursor)

    log.info("Converteren natuurlijk_persoon")
    _converteer_natuurlijk_persoon(cursor)

    log.info("Converteren NIET natuurlijk_persoon")
    _converteer_niet_natuurlijk_persoon(cursor)

    log.info("Converteren persoon")
    _converteer_persoon(cursor)

    log.info("Converteren functievervulling")
    _converteer_functievervulling(cursor)

    log.info("Converteer eigenaren")
    _converteer_mac_eigenaar_id(cursor)

    # eigenaren zitten niet in zonde export..
    log.info("Converteer onbekende mac mks eigenaren")
    _converteer_onbekende_mac_eigenaar_id(cursor)

    # Dropall outside of Amsterdam
    # if not settings.TESTING:
    if not keep_outside_amsterdam:
        log.info("Verwijder vestigingen met bezoekadres buiten Amsterdam")
        deleted = Vestiging.objects.exclude(
            bezoekadres__volledig_adres__endswith='Amsterdam').delete()
        log.info(deleted)


def fill_location_with_bag():
    """
    Update attributes of location data with BAG data.

    NOTE:

    When search correction is done locations contain
    new bag_id / num_id and with this funtion
    the fields get updated with bag data.

    """
    with db.connection.cursor() as cursor:
        log.info("VUL geo tabel locaties met bag geometrie")
        _update_location_table_with_bag(cursor)


def fill_geo_table():
    with db.connection.cursor() as cursor:
        # bouw de hr_geo_table
        log.info("Bouw geo tabel vestigingen met SBI informatie")
        _build_joined_geo_table(cursor)


def clear_autocorrect():
    with db.connection.cursor() as cursor:
        log.info("Empty geo tabel locaties van autocorrect: bag geometrie")
        _clear_autocorrected_results(cursor)


def _converteer_locaties(cursor):
    Locatie.objects.all().delete()
    cursor.execute("""
INSERT INTO hr_locatie (
  id,
  volledig_adres,
  toevoeging_adres,
  afgeschermd,
  postbus_nummer,
  bag_numid,
  bag_vbid,
  bag_nummeraanduiding,
  bag_adresseerbaar_object,
  straat_huisnummer,
  postcode_woonplaats,
  regio,
  land,
  geometrie,
  straatnaam,
  postcode,
  huisnummer,
  huisnummertoevoeging,
  huisletter,
  plaats
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
      identificatieaoa,
      identificatietgo,
      'https://api.data.amsterdam.nl/bag/nummeraanduiding/' ||
            identificatieaoa || '/',
      'https://api.data.amsterdam.nl/bag/verblijfsobject/' ||
            identificatietgo || '/',
      straathuisnummer,
      postcodewoonplaats,
      regio,
      land,
      geopunt,
      straatnaam,
      postcode,
      huisnummer,
      huisnummertoevoeging,
      huisletter,
      plaats
    FROM kvkadrm00
        """)


def _converteer_onderneming(cursor):
    Onderneming.objects.all().delete()
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
    vh.vesid,
    h.hdnid
  FROM kvkveshdnm00 vh LEFT JOIN kvkhdnm00 h ON vh.veshdnid = h.hdnid
  WHERE h.hdnid IS NOT NULL
    """)


def _converteer_mac_communicatiegegevens(cursor, i):
    _converteer_any_communicatiegegevens(
        cursor, i, 'macid', 'kvkmacm00', 'maatschappelijkeactiviteit')


def _converteer_ves_communicatiegegevens(cursor, i):
    _converteer_any_communicatiegegevens(
        cursor, i, 'vesid', 'kvkvesm00', 'vestiging')


def _converteer_any_communicatiegegevens(
        cursor, i, id_col, source, target):
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

    coalesce(v.eerstehandelsnaam, v.naam),
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
    sbicodehoofdactiviteit,
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
    sbicodenevenactiviteit{index},
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


def _converteer_hoofdvestiging(cursor):
    cursor.execute("""
UPDATE hr_maatschappelijkeactiviteit m
SET hoofdvestiging_id = v.id
FROM hr_vestiging v
WHERE v.maatschappelijke_activiteit_id = m.id
  AND v.hoofdvestiging
    """)


def _converteer_persoon(cursor):
    cursor.execute("""
INSERT INTO hr_persoon (
    id,
    typering,
    rol,
    rechtsvorm,
    uitgebreide_rechtsvorm,
    volledige_naam,
    soort,
    reden_insolvatie,
    datumuitschrijving,
    nummer,
    toegangscode,
    faillissement,
    natuurlijkpersoon_id,
    niet_natuurlijkpersoon_id
) SELECT
    prsid,
    typering,
    rol,
    persoonsrechtsvorm,
    uitgebreiderechtsvorm,
    volledigenaam,
    soort,
    redeninsolvatie,
    to_date(to_char(datumuitschrijving, '99999999'), 'YYYYMMDD'),
    nummer,
    toegangscode,
    CASE faillissement
        WHEN 'Ja' THEN TRUE
        ELSE FALSE
    END,
    CASE typering
        WHEN 'natuurlijkPersoon' THEN prsid
        ELSE NULL
    END,
    CASE typering != 'natuurlijkPersoon'
        WHEN TRUE THEN prsid
        ELSE NULL
    END
  FROM kvkprsm00
    """)


def _converteer_natuurlijk_persoon(cursor):
    cursor.execute("""
INSERT INTO hr_natuurlijkpersoon (
    id,
    geslachtsnaam,
    geslachtsaanduiding,
    voornamen,
    huwelijksdatum,
    geboortedatum,
    geboorteplaats,
    geboorteland
) SELECT
    prsid,
    geslachtsnaam,
    geslachtsaanduiding,
    voornamen,
    to_date(to_char(huwelijksdatum, '99999999'), 'YYYYMMDD'),
    to_date(to_char(geboortedatum, '99999999'), 'YYYYMMDD'),
    geboorteplaats,
    geboorteland
  FROM kvkprsm00 WHERE typering = 'natuurlijkPersoon'
    """)


def _converteer_niet_natuurlijk_persoon(cursor):
    cursor.execute("""
INSERT INTO hr_nietnatuurlijkpersoon (
    id,
    rsin,
    verkorte_naam,
    ook_genoemd
) SELECT
    prsid,
    rsin,
    verkortenaam,
    ookgenoemd
  FROM kvkprsm00 WHERE typering != 'natuurlijkPersoon'
    """)


def _converteer_functievervulling(cursor):
    cursor.execute("""
INSERT INTO hr_functievervulling (
    id,
    functietitel,
    heeft_aansprakelijke_id,
    is_aansprakelijke_id,
    soortbevoegdheid
) SELECT
    ashid,
    functie,
    prsidh,
    prsidi,
    soort
  FROM kvkprsashm00
    """)


def _converteer_mac_eigenaar_id(cursor):
    cursor.execute("""
UPDATE hr_maatschappelijkeactiviteit hrm
SET eigenaar_id = m.prsid
FROM kvkmacm00 m
WHERE m.macid = hrm.id AND EXISTS (
    SELECT * FROM hr_persoon WHERE id = m.prsid)
    """)


def _converteer_onbekende_mac_eigenaar_id(cursor):
    cursor.execute("""
UPDATE hr_maatschappelijkeactiviteit hrm
SET eigenaar_mks_id = m.prsid
FROM kvkmacm00 m
WHERE m.macid = hrm.id AND NOT EXISTS (
    SELECT * FROM hr_persoon WHERE id = m.prsid)
    """)


def _update_location_table_with_bag(cursor):
    cursor.execute("""
UPDATE hr_locatie loc
    SET geometrie = bag.geometrie,
        huisnummer = bag.huisnummer,
        huisletter = bag.huisletter,
        huisnummertoevoeging = bag.huisnummer_toevoeging,
        straatnaam = bag._openbare_ruimte_naam,
        postcode = bag.postcode
FROM (select v.id,
      v.landelijk_id,
      n.huisnummer,
      n.huisletter,
      n.huisnummer_toevoeging,
      n._openbare_ruimte_naam,
      n.postcode,
      v.geometrie
      FROM bag_nummeraanduiding n, bag_verblijfsobject v
      WHERE n.verblijfsobject_id = v.id AND n.hoofdadres) bag
WHERE bag.landelijk_id = loc.bag_vbid OR bag.landelijk_id = loc.bag_numid
    """)


def _clear_autocorrected_results(cursor):
    cursor.execute("""
UPDATE hr_locatie
    SET geometrie = NULL,
        correctie = NULL,
        bag_vbid = NULL,
        bag_numid = NULL,
        correctie_level = NULL
WHERE correctie IS NOT NULL
    """)


def _build_joined_geo_table(cursor):
    """
    We create vestigingen geo table for use with
    mapserver and geo_views and also dataselectie.
    """

    # Make sure we have sbi codes
    assert SBICodeHierarchy.objects.count() > 0

    # clear existing geovestigingen
    GeoVestigingen.objects.all().delete()

    cursor.execute(f"""
INSERT INTO hr_geovestigingen (
    vestigingsnummer,

    sbi_code,
    activiteitsomschrijving,

    subtype,
    naam,
    uri,
    hoofdvestiging,
    locatie_type,
    geometrie,
    sbi_tree,
    sbi_main_category,
    sbi_sub_category,
    sbi_sub_sub_category,

    q1,  /* question 1 */
    q2,  /* question 2 */
    q3,  /* question 3 */

    postadres_id,
    bezoekadres_id,
    bag_vbid,
    correctie
) SELECT
    vs.vestigingsnummer,
    a.sbi_code,
    a.activiteitsomschrijving,

    CAST('handelsregister/vestiging' AS text) as subtype,

    vs.naam,
    '{settings.DATAPUNT_API_URL}' || 'handelsregister/vestiging/' ||
        vs.vestigingsnummer || '/' AS uri,
    vs.hoofdvestiging,

    CASE
      WHEN vs.bezoekadres_id = loc.id THEN 'B'
      WHEN vs.postadres_id = loc.id THEN 'P'
    END as locatie_type,

    loc.geometrie as geometrie,

    sbi.sbi_tree,
    sbi.sbi_tree->'l1'->>0 as sbi_main_category,
    sbi.sbi_tree->'l2'->>0 as sbi_sub_category,
    sbi.sbi_tree->'l3'->>0 as sbi_sub_sub_category,

    sbi.qa_tree->>'q1'::text as q1,
    sbi.qa_tree->>'q2'::text as q2,
    sbi.qa_tree->>'q3'::text as q3,

    vs.postadres_id,
    vs.bezoekadres_id,
    loc.bag_vbid,
    loc.correctie

  FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id)
        AND ST_IsValid(loc.geometrie)
    JOIN sbicodes_sbicodehierarchy sbi
    ON sbi.code = a.sbi_code
    """)
