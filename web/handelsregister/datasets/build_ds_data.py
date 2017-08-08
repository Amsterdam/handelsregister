import logging
from datasets.hr import models, serializers

log = logging.getLogger(__name__)


def get_vestigingen(offset: int = 0, size: int = None) -> object:
    """
    Generates a query set to build json data for dataselectie
    An optional offset and size parameters can be given to limit
    the size of the queryset
    """
    qs = models.Vestiging.objects \
        .select_related('maatschappelijke_activiteit') \
        .select_related('bezoekadres') \
        .select_related('postadres') \
        .prefetch_related('activiteiten') \
        .prefetch_related('activiteiten__sbi_code_tree') \
        .prefetch_related('handelsnamen') \
        .order_by('id')
    if size:
        qs = qs[offset:size]
    return qs


def write_dataselectie_data(step: int = 500):
    """
    Writes dataselectie data to the database from the HR data

    The step parameter determings the size of each
    queryset to handle
    """
    # Deleting all previous data
    models.DataSelectie.objects.all().delete()
    offset = 0
    qs = get_vestigingen(offset, offset+step)
    while qs:
        bulk = []
        for item in qs:
            bag_numid = item.locatie.bag_numid

            bulk.append(
                models.DataSelectie(
                    id=item.id,
                    bag_numid=bag_numid,
                    api_json=serializers.VestigingDataselectie(item).data
                )
            )

        # Using bulk save to save on ORM handling
        # and db connections
        models.DataSelectie.objects.bulk_create(bulk)
        offset += step  # Moving to the next step
        log.debug(f'{offset} items imported')
        qs = get_vestigingen(offset, offset+step)
