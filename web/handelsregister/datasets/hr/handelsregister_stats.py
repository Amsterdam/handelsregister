"""
Collect status counts about location data in the Handelregister
"""
import os.path
import json
import logging
from django.db import connection

from . import models


LOG = logging.getLogger(__name__)

tmp_json = '/tmp/stats.json'
# keep track of counts
STATS = []

# load historic counts
if os.path.exists(tmp_json):
    with open(tmp_json, 'r') as stats:
        STATS = json.load(stats)


def location_stats():
    """
    Collect and log count statistic abour the quality
    of he HR location / adres data
    """

    LOG.debug('locatie counts..')

    all_locations = models.Locatie.objects.all()
    empty_loc = all_locations.filter(geometrie__isnull=True)
    empty_loc_no_postbus = empty_loc.exclude(
        volledig_adres__startswith="Postbus")
    postbus_loc = all_locations.filter(volledig_adres__startswith="Postbus")

    return dict(
        a_loc=all_locations.count(),
        a_loc_zg=empty_loc_no_postbus.count(),
        a_loc_postbus=postbus_loc.count()
    )


def sql_count(table):

    c_stmt = f"SELECT COUNT(*) FROM {table};"
    count = 0

    with connection.cursor() as c:
        c.execute(c_stmt)
        row = c.fetchone()
        count += row[0]
        LOG.debug('COUNT %-6s %s', count, table)

    return count


def check_table_targets():
    """
    For each table we have a target Count. Validate this.
    """
    tables_target = [
        # Count  table
        (412592, "hr_activiteit"),
        (304922, "hr_commercielevestiging"),
        (409539, "hr_communicatiegegevens"),
        (199378, "hr_dataselectie"),
        (45872, "hr_functievervulling"),
        (559616, "hr_geovestigingen"),
        (366330, "hr_handelsnaam"),
        (656598, "hr_locatie"),
        (323935, "hr_maatschappelijkeactiviteit"),
        (310000, "hr_maatschappelijkeactiviteit_activiteiten"),
        (67414, "hr_maatschappelijkeactiviteit_communicatiegegevens"),
        (176619, "hr_natuurlijkpersoon"),
        (6760, "hr_nietcommercielevestiging"),
        (193172, "hr_nietnatuurlijkpersoon"),
        (271055, "hr_onderneming"),
        (366330, "hr_onderneming_handelsnamen"),
        (369808, "hr_persoon"),
        (217397, "hr_vestiging"),
        (321073, "hr_vestiging_activiteiten"),
        (269566, "hr_vestiging_communicatiegegevens"),
        (273455, "hr_vestiging_handelsnamen"),
    ]

    check_table_counts(tables_target)


def check_geo_table_target_counts():

    geo_table_targets = [
        (18470, "geo_hr_vestiging_locaties_bouw"),
        (15590, "geo_hr_vestiging_locaties_bouw_naam"),
        (57052, "geo_hr_vestiging_locaties_cultuur_sport_recreatie"),
        (49565, "geo_hr_vestiging_locaties_cultuur_sport_recreatie_naam"),
        (113379, "geo_hr_vestiging_locaties_financiele_dienstverlening_verhuur"),     # noqa
        (77173, "geo_hr_vestiging_locaties_financiele_dienstverlening_verhuur_na"),  # noqa
        (73540, "geo_hr_vestiging_locaties_handel_vervoer_opslag"),
        (53340, "geo_hr_vestiging_locaties_handel_vervoer_opslag_naam"),
        (19561, "geo_hr_vestiging_locaties_horeca"),
        (17677, "geo_hr_vestiging_locaties_horeca_naam"),
        (46313, "geo_hr_vestiging_locaties_informatie_telecommunicatie"),
        (34982, "geo_hr_vestiging_locaties_informatie_telecommunicatie_naam"),
        (782, "geo_hr_vestiging_locaties_landbouw"),
        (396, "geo_hr_vestiging_locaties_landbouw_naam"),
        (329372, "geo_hr_vestiging_locaties_naam"),
        (61864, "geo_hr_vestiging_locaties_overheid_onderwijs_zorg"),
        (53511, "geo_hr_vestiging_locaties_overheid_onderwijs_zorg_naam"),
        (145, "geo_hr_vestiging_locaties_overige"),
        (17796, "geo_hr_vestiging_locaties_overige_naam"),
        (11329, "geo_hr_vestiging_locaties_persoonlijke_dienstverlening"),
        (10574, "geo_hr_vestiging_locaties_persoonlijke_dienstverlening_naam"),
        (11707, "geo_hr_vestiging_locaties_productie_installatie_reparatie"),
        (12107, "geo_hr_vestiging_locaties_productie_installatie_reparatie_naam"),  # noqa
        (121804, "geo_hr_vestiging_locaties_zakelijke_dienstverlening"),
        (114618, "geo_hr_vestiging_locaties_zakelijke_dienstverlening_naam"),
    ]

    check_table_counts(geo_table_targets)


def check_table_counts(table_data):
    for target, table in table_data:
        count = sql_count(table)
        if count < target - 5000 and count > 0:
            LOG.debug(
                'Table Count Mismatch. %s %s is not around %s',
                table, count, target
            )
            raise ValueError()


def check_sub_counts(counts):
    """
    Validate counts for variables / derived counts so
    we can validate our import process
    """

    variable_target = [
        # Min, Max, variable
        (0, 300, 'ves_adam_zg'),
        (0, 150, 'ves_adam_zg_b')
    ]

    for _min, _max, variable in variable_target:
        count = counts[variable]
        if _min < count < _max:

            LOG.info(
                'Count OK for %s %d < %d < %d',
                variable, _min, count, _max
            )
            continue

        LOG.error(
            'Count FAILED for %s %d < %d < %d',
            variable, _min, count, _max
        )
        raise ValueError


def vestiging_stats():
    """
    Collect and log count statistic abour the quality
    of he HR location / adres data
    """
    LOG.debug('ves counts..')

    hr_ves = models.Vestiging.objects.all()

    all_locations = models.Locatie.objects.all()

    ves_locaties = all_locations.extra(
        tables=['hr_vestiging'],
        where=[
            '''"hr_vestiging"."bezoekadres_id"="hr_locatie"."id"
            OR "hr_vestiging"."postadres_id"="hr_locatie"."id"
            AND"hr_vestiging"."datum_einde" is null
            ''',
        ])

    ves_locaties_bezoek = all_locations.extra(
        tables=['hr_vestiging'],
        where=[
            '''"hr_vestiging"."bezoekadres_id"="hr_locatie"."id"
            AND"hr_vestiging"."datum_einde" is null
            '''])

    ves_locaties_post = all_locations.extra(
        tables=['hr_vestiging'],
        where=['"hr_vestiging"."postadres_id"="hr_locatie"."id"'])

    ves_postbus = ves_locaties.filter(
        volledig_adres__startswith="Postbus")

    ves_zonder_postbus = ves_locaties.exclude(
        volledig_adres__startswith="Postbus")

    missing_ves_locaties = ves_zonder_postbus.extra(
        where=['"hr_locatie"."geometrie" is null']
    ).exclude(volledig_adres__startswith="Postbus")

    missing_ves_in_amsterdam = missing_ves_locaties.extra(
        where=['"hr_locatie"."volledig_adres" like \'%%Amsterdam\'']
    )

    missing_ves_bezoek_adam = all_locations.extra(
        tables=['hr_vestiging'],
        where=[
            '"hr_vestiging"."bezoekadres_id"="hr_locatie"."id"',
            '"hr_locatie"."geometrie" is null',
            '"hr_vestiging"."datum_einde" is null',
            '"hr_locatie"."volledig_adres" like \'%%Amsterdam\''
        ]
    )

    missing_ves_bezoek_bag_id_adam = all_locations.extra(
        tables=['hr_vestiging'],
        where=[
            '"hr_vestiging"."bezoekadres_id"="hr_locatie"."id"',
            '"hr_locatie"."bag_vbid" is null',
            '"hr_locatie"."volledig_adres" like \'%%Amsterdam\''
        ]
    )
    missing_ves_bezoek_num_id_adam = all_locations.extra(
        tables=['hr_vestiging'],
        where=[
            '"hr_vestiging"."bezoekadres_id"="hr_locatie"."id"',
            '"hr_locatie"."bag_numid" is null',
            '"hr_locatie"."volledig_adres" like \'%%Amsterdam\''
        ]
    )

    ves_loc_bag_id = missing_ves_locaties.extra(
        where=['"hr_locatie"."bag_vbid" is not null'])

    ves_loc_num_id = missing_ves_locaties.extra(
        where=['"hr_locatie"."bag_numid" is not null'])

    return dict(
        hr_ves=hr_ves.count(),

        a_ves=ves_locaties.count(),
        a_ves_b=ves_locaties_bezoek.count(),
        a_ves_p=ves_locaties_post.count(),
        a_ves_pb=ves_postbus.count(),
        a_ves_zg=missing_ves_locaties.count(),
        a_ves_zg_mbgid=ves_loc_bag_id.count(),
        a_ves_zg_mnmid=ves_loc_num_id.count(),

        ves_adam_zg=missing_ves_in_amsterdam.count(),
        ves_adam_zg_b=missing_ves_bezoek_adam.count(),
        ves_adam_zvb_id=missing_ves_bezoek_bag_id_adam.count(),
        ves_adam_znum_id=missing_ves_bezoek_num_id_adam.count(),
    )


def mac_stats():
    """
    Collect and log count statistic abour the quality
    of he HR location / adres data
    """

    LOG.debug('mac counts..')

    macs = models.MaatschappelijkeActiviteit.objects.all()

    mac_locaties = macs.extra(
        tables=['hr_locatie'],
        where=['''
        "hr_maatschappelijkeactiviteit"."bezoekadres_id"="hr_locatie"."id"
        OR "hr_maatschappelijkeactiviteit"."postadres_id"="hr_locatie"."id"
        '''])

    mac_locaties_amsterdam = mac_locaties.extra(
        where=['"hr_locatie"."volledig_adres" like \'%%Amsterdam\'']
    )

    mac_locaties_amsterdam_nogeo = mac_locaties_amsterdam.extra(
        where=['"hr_locatie"."geometrie" is null'])

    missing_mac_locaties = mac_locaties.extra(
        where=['"hr_locatie"."geometrie" is null'])

    return dict(
        a_mac=mac_locaties.count(),
        a_mac_zg=missing_mac_locaties.count(),
        mac_adam=mac_locaties_amsterdam.count(),
        mac_adam_zg=mac_locaties_amsterdam_nogeo.count(),
    )


def geovestigingen_stats():
    """
    Geo vestigingen op de kaart
    """

    geoves = models.GeoVestigingen.objects.all()
    dataselectie = models.DataSelectie.objects.all()

    geoves_sbi = geoves.filter(sbi_code__isnull=True)

    geoves_post = geoves.filter(locatie_type='P')
    geoves_bezoek = geoves.filter(locatie_type='B')

    return dict(
        ves_kaart=geoves.count(),
        ves_kaart_zsbi=geoves_sbi.count(),
        ves_kaart_p=geoves_post.count(),
        ves_kaart_b=geoves_bezoek.count(),
        ves_ds=dataselectie.count()
    )


def log_rapport_counts(action='', fail_on_wrong_target=False):
    """
    Log the count rapports available
    """

    # validate table counts
    if fail_on_wrong_target:
        check_table_targets()
        check_geo_table_target_counts()

    counts = {'actie': action}
    counts.update(location_stats())
    counts.update(vestiging_stats())
    counts.update(mac_stats())
    counts.update(geovestigingen_stats())

    # validate counts
    if fail_on_wrong_target:
        check_sub_counts(counts)

    STATS.append(counts)

    if len(STATS) > 6:
        STATS.pop(0)

    if action == '':
        counts['actie'] = len(STATS)

    # update stats with latest status
    with open(tmp_json, 'w') as thefile:
        json.dump(STATS, thefile)

    count_lines = {
    }

    def new_row(row, cell):
        return '%s   %-9s' % (row, cell)

    for i, countx in enumerate(STATS):
        for key, count in countx.items():
            old_row = count_lines.get(key, '')
            count_lines[key] = new_row(old_row, count)

    LOG.debug("""

    Actie                        {actie}

    Alle HR Locaties             {a_loc}
    zonder geometrie             {a_loc_zg}
    postbus                      {a_loc_postbus}

    Alle vestigingen in hr       {hr_ves}

    Totaal Vestiging locaties    {a_ves}

    waarvan          bezoek      {a_ves_b}
    waarvan          post        {a_ves_p}
    waarvan          postbus     {a_ves_pb}

    zonder geometrie             {a_ves_zg}
    zonder geo maar met bag id   {a_ves_zg_mbgid}
    zonder geo maar met num id   {a_ves_zg_mnmid}

    zonder geometrie Amsterdam   {ves_adam_zg}
    waarvan bezoek               {ves_adam_zg_b}
    geen bag_vbid/landelijkid    {ves_adam_zvb_id}
    geen bag_numid/landelijkid   {ves_adam_znum_id}

    Totaal Mac locaties          {a_mac}
    zonder geometrie             {a_mac_zg}

    in Amsterdam                 {mac_adam}
    in Amsterdam zonder GEO      {mac_adam_zg}

    Van macs hebben we (nog) geen sbi_codes !!

    Vestigingen op de kaart

    Totaal voor op de kaart      {ves_kaart}
    zonder sbi                   {ves_kaart_zsbi}
    post   locaties              {ves_kaart_p}
    bezoek locaties              {ves_kaart_b}

    Dataselectie                 {ves_ds}
             """.format(**count_lines))
