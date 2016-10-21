"""
Collect counts about location data of HR
"""


import logging

from . import models


LOG = logging.getLogger(__name__)


def location_stats():
    """
    Collect and log count statistic abour the quality
    of he HR location / adres data
    """
    all_locations = models.Locatie.objects.all()
    empty_loc = all_locations.filter(geometrie__isnull=True)
    empty_loc_no_postbus = empty_loc.exclude(
        volledig_adres__startswith="Postbus")
    postbus_loc = all_locations.filter(volledig_adres__startswith="Postbus")

    locatie_counts = [
        all_locations.count(),
        empty_loc_no_postbus.count(),
        postbus_loc.count()
    ]

    LOG.debug("""

    Alle HR Locaties           %-9i
    zonder geometrie           %-9i
    postbus                    %-9i

                """, *locatie_counts)


def vestiging_stats():
    """
    Collect and log count statistic abour the quality
    of he HR location / adres data
    """

    all_locations = models.Locatie.objects.all()

    ves_locaties = all_locations.extra(
        tables=['hr_vestiging'],
        where=[
            '''"hr_vestiging"."bezoekadres_id"="hr_locatie"."id"
            OR "hr_vestiging"."postadres_id"="hr_locatie"."id" ''',
        ])

    ves_postbus = ves_locaties.exclude(volledig_adres__startswith="Postbus")

    missing_ves_locaties = ves_locaties.extra(
        where=['"hr_locatie"."geometrie" is null']
    ).exclude(volledig_adres__startswith="Postbus")

    missing_ves_in_amsterdam = missing_ves_locaties.extra(
        where=['"hr_locatie"."volledig_adres" like \'%%Amsterdam\'']
    )

    ves_loc_bag_id = missing_ves_locaties.extra(
        where=['"hr_locatie"."bag_vbid" is not null'])

    ves_loc_num_id = missing_ves_locaties.extra(
        where=['"hr_locatie"."bag_numid" is not null'])

    ves_counts = [
        ves_locaties.count(),
        ves_postbus.count(),
        missing_ves_locaties.count(),
        ves_loc_bag_id.count(),
        ves_loc_num_id.count(),
        missing_ves_in_amsterdam.count()
    ]

    LOG.debug("""

    Totaal Vestiging locaties  %-9i
    waarvan postbus            %-9i

    zonder geometrie           %-9i
    zonder geo maar met bag id %-9i
    zonder geo maar met num id %-9i

    zonder geometrie Amsterdam %-9i

                """, *ves_counts)

    return ves_counts


def mac_stats():
    """
    Collect and log count statistic abour the quality
    of he HR location / adres data
    """

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

    missing_mac_locaties = mac_locaties.extra(
        where=['"hr_locatie"."geometrie" is null'])

    mac_counts = [
        mac_locaties.count(),
        missing_mac_locaties.count(),
        mac_locaties_amsterdam.count()
    ]

    LOG.debug("""

    Totaal Mac locaties        %-9i
    zonder geometrie           %-9i

    in Amsterdam               %-9i

    Van macs hebben we geen sbi_codes

                """, *mac_counts)
