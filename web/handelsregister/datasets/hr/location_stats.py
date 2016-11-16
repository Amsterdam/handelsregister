"""
Collect status counts about location data in the Handelregister
"""


import os.path
import json
import logging

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

    return [
        all_locations.count(),
        empty_loc_no_postbus.count(),
        postbus_loc.count()
    ]


def vestiging_stats():
    """
    Collect and log count statistic abour the quality
    of he HR location / adres data
    """
    LOG.debug('ves counts..')

    all_locations = models.Locatie.objects.all()

    ves_locaties = all_locations.extra(
        tables=['hr_vestiging'],
        where=[
            '''"hr_vestiging"."bezoekadres_id"="hr_locatie"."id"
            OR "hr_vestiging"."postadres_id"="hr_locatie"."id" ''',
        ])

    ves_locaties_bezoek = all_locations.extra(
        tables=['hr_vestiging'],
        where=['''"hr_vestiging"."bezoekadres_id"="hr_locatie"."id"'''])

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
            '"hr_locatie"."volledig_adres" like \'%%Amsterdam\''
        ]
    )

    ves_loc_bag_id = missing_ves_locaties.extra(
        where=['"hr_locatie"."bag_vbid" is not null'])

    ves_loc_num_id = missing_ves_locaties.extra(
        where=['"hr_locatie"."bag_numid" is not null'])

    return [
        ves_locaties.count(),
        ves_locaties_bezoek.count(),
        ves_locaties_post.count(),
        ves_postbus.count(),
        missing_ves_locaties.count(),
        ves_loc_bag_id.count(),
        ves_loc_num_id.count(),
        missing_ves_in_amsterdam.count(),
        missing_ves_bezoek_adam.count(),
    ]


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

    return [
        mac_locaties.count(),
        missing_mac_locaties.count(),
        mac_locaties_amsterdam.count(),
        mac_locaties_amsterdam_nogeo.count(),
    ]


def geovestigingen_stats():
    """
    Geo vestigingen op de kaart
    """

    geoves = models.GeoVestigingen.objects.all()

    geoves_sbi = geoves.filter(
        sbi_code_int__isnull=True)

    geoves_post = geoves.filter(locatie_type='P')
    geoves_bezoek = geoves.filter(locatie_type='B')

    return [
        geoves.count(),
        geoves_sbi.count(),
        geoves_post.count(),
        geoves_bezoek.count(),
    ]


def log_rapport_counts():
    """
    Log the count rapports available
    """

    counts = location_stats()
    counts.extend(vestiging_stats())
    counts.extend(mac_stats())
    counts.extend(geovestigingen_stats())

    STATS.append(counts)

    if len(STATS) > 6:
        STATS.pop(0)

    # update stats with latest status
    with open(tmp_json, 'w') as thefile:
        json.dump(STATS, thefile)

    header = ""
    count_lines = ['' for c in counts]

    def new_row(row, cell):
        return '%s   %-9i' % (row, cell)

    for i, countx in enumerate(STATS):
        header = new_row(header, i)
        count_lines = map(new_row, count_lines, countx)

    count_lines = list(count_lines)
    count_lines.insert(0, header)

    LOG.debug("""

    Telmoment                    %s

    Alle HR Locaties             %s
    zonder geometrie             %s
    postbus                      %s


    Totaal Vestiging locaties    %s
    waarvan          bezoek      %s
    varvan           post        %s
    warvan           postbus     %s

    zonder geometrie             %s
    zonder geo maar met bag id   %s
    zonder geo maar met num id   %s

    zonder geometrie Amsterdam   %s
    waarvan bezoek               %s

    Totaal Mac locaties          %s
    zonder geometrie             %s

    in Amsterdam                 %s
    in Amsterdam zonder GEO      %s

    Van macs hebben we (nog) geen sbi_codes !!

    Vestigingen op de kaart

    Totaal voor op de kaart      %s
    zonder sbi                   %s
    post   locaties              %s
    bezoek locaties              %s
             """, *count_lines)
