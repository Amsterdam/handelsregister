"""
Collect counts about location data of HR
"""


import os.path
import json
import logging
import gevent

from . import models


LOG = logging.getLogger(__name__)

# keep track of counts
STATS = []

# load historic counts
if os.path.exists('stats.json'):
    with open('stats.json', 'r') as stats:
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

    jobs = [
        gevent.spawn(all_locations.count),
        gevent.spawn(empty_loc_no_postbus.count),
        gevent.spawn(postbus_loc.count)
    ]

    gevent.joinall(jobs)

    locatie_counts = [job.value for job in jobs]

    return locatie_counts


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

    ves_loc_bag_id = missing_ves_locaties.extra(
        where=['"hr_locatie"."bag_vbid" is not null'])

    ves_loc_num_id = missing_ves_locaties.extra(
        where=['"hr_locatie"."bag_numid" is not null'])

    jobs = [
        gevent.spawn(ves_locaties.count),
        gevent.spawn(ves_postbus.count),
        gevent.spawn(missing_ves_locaties.count),
        gevent.spawn(ves_loc_bag_id.count),
        gevent.spawn(ves_loc_num_id.count),
        gevent.spawn(missing_ves_in_amsterdam.count)
    ]

    gevent.joinall(jobs)

    return [job.value for job in jobs]


def mac_stats():
    """
    Collect and log count statistic abour the quality
    of he HR location / adres data
    """
    LOG.debug('mac counts..')

    macs = models.MaatschappelijkeActiviteit.objects.all()

    mac_locaties = macs.extra(
        tables=['hr_locatie'],
        where=[
            '''"hr_maatschappelijkeactiviteit"."bezoekadres_id"="hr_locatie"."id"
            OR "hr_maatschappelijkeactiviteit"."postadres_id"="hr_locatie"."id"
            '''])

    mac_locaties_amsterdam = mac_locaties.extra(
        where=['"hr_locatie"."volledig_adres" like \'%%Amsterdam\'']
    )

    mac_locaties_amsterdam_nogeo = mac_locaties_amsterdam.extra(
        where=['"hr_locatie"."geometrie" is null'])

    missing_mac_locaties = mac_locaties.extra(
        where=['"hr_locatie"."geometrie" is null'])

    jobs = [
        gevent.spawn(mac_locaties.count),
        gevent.spawn(missing_mac_locaties.count),
        gevent.spawn(mac_locaties_amsterdam.count),
        gevent.spawn(mac_locaties_amsterdam_nogeo.count),
    ]

    gevent.joinall(jobs)

    mac_counts = [job.value for job in jobs]

    return mac_counts


def geovestigingen_stats():
    """
    Geo vestigingen op de kaart
    """

    geoves = models.GeoVestigingen.objects.all()

    geoves_sbi = geoves.filter(
        sbi_code_int__isnull=True)

    return [geoves.count(), geoves_sbi.count()]


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
    with open('stats.json', 'w') as thefile:
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
    waarvan postbus              %s

    zonder geometrie             %s
    zonder geo maar met bag id   %s
    zonder geo maar met num id   %s

    zonder geometrie Amsterdam   %s


    Totaal Mac locaties          %s
    zonder geometrie             %s

    in Amsterdam                 %s
    in Amsterdam zonder GEO      %s

    Van macs hebben we (nog) geen sbi_codes !!

    Vestigingen op de kaart

    Totaal voor op de kaart      %s
    zonder sbi                   %s



             """, *count_lines)