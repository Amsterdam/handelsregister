# Python
from datetime import datetime, date
from decimal import Decimal
import logging
import time

from itertools import groupby

# Packages
from django import db
from django.contrib.gis.geos.point import Point
# Project
from datasets.hr import models, serializers


log = logging.getLogger(__name__)


def get_vestigingen(offset=0: int, size=None: int) -> object:
    """
    Generates a query set to build json data for dataselectie
    An optional offset and size parameters can be given to limit
    the size of the queryset
    """
    qs = models.Vestiging.objects.select_related('maatschappelijke_activiteit') \
        .select_related('bezoekadres') \
        .select_related('postadres') \
        #.prefetch_related('communicatiegegevens') \
        .prefetch_related('activiteiten') \
        .prefetch_related('handelsnamen')
    if size:
        qs = qs[offset:size]
    return qs


def write_dataselectie_data(step=10000: int):
    """
    Writes dataselectie data to the database from the HR data

    The step parameter determings the size of each queryset to handle
    """
    # Deleting all previous data
    models.Dataselectie.objects.all().delete()
    offset = 0
    while qs = get_vestigingen(offset, offset+step):
        bulk = []  # @TODO Typing
        for item in qs:
            bulk.append(models.Dataselectie(
                id = item.id,
                bag_numid = item.locatie.bag_num_id,
                api_json=serializers.VestigingDataselectie(item).data)
            )
        # Using bulk save to save on ORM handling and db connections
        models.Dataselectie.objects.bulk_create(bulk)
        offset += step  # Moving to the next step
