import logging

from django.conf import settings

from datasets.hr import models, serializers

from django.db.models.functions import Cast
from django.db.models import F
# from django.db.models.functions import Substr
from django.db.models import BigIntegerField


log = logging.getLogger(__name__)

tracking = {
    'last_id': None,
    'batch_size': 100,
}


def get_vestigingen(offset: int = 0) -> object:
    """
    Generates a query set to build json data for dataselectie
    An optional offset and size parameters can be given to limit
    the size of the queryset
    """
    qs = (
        models.Vestiging.objects
        .select_related('maatschappelijke_activiteit')
        .select_related('maatschappelijke_activiteit__eigenaar')
        .select_related('bezoekadres')
        .select_related('postadres')
        .select_related('commerciele_vestiging')
        .select_related('niet_commerciele_vestiging')
        .prefetch_related('activiteiten')
        .prefetch_related('activiteiten__sbi_code_tree')
        .prefetch_related('handelsnamen')
        .filter(datum_einde__isnull=True)
        .order_by('id')
    )

    return qs


def get_maatschappelijke_activiteiten() -> object:
    """
    Build query to return Mac in Amsterdam.
    """

    qs = (
        models.MaatschappelijkeActiviteit.objects
        .filter(datum_einde__isnull=True)
        .select_related('bezoekadres')
        .select_related('postadres')
        .select_related('hoofdvestiging')
        .select_related('eigenaar')
        .select_related('onderneming')
        .prefetch_related('activiteiten')
        .prefetch_related('communicatiegegevens')
        .order_by('id')
    )

    qs_p = (
        qs.filter(bezoekadres__plaats='Amsterdam')
    )
    qs_b = (
        qs.filter(postadres__plaats='Amsterdam')
    )

    return qs_p | qs_b


def generate_qs_parts(qs, modulo, modulo_value):
    """ generate qs within min_id and max_id

        modulo and modulo_value determin which chuncks
        are teturned.

        if partial = 1/3

        then this function only returns chuncks index i for which
        modulo i % 3 == 1
    """
    if modulo != 1:

        qs_s = (
            qs.annotate(idmod=Cast('id', BigIntegerField()))
            .annotate(idmod=F('idmod') % modulo)
            .filter(idmod=modulo_value)
        )

    else:
        qs_s = qs

    log.debug('COUNT %d', qs_s.count())

    return generate_qs(qs_s)


def generate_qs(qs_s):
    """
    Chunk qs
    """
    # gets updates when we save object in es
    last_id = None
    # batch_size = settings.BATCH_SETTINGS['batch_size']
    batch_size = tracking['batch_size']
    loopidx = 0

    while True:

        loopidx += 1
        last_id = tracking['last_id']

        if not last_id:
            qs_ss = qs_s[:batch_size]
        else:
            qs_ss = qs_s.filter(id__gt=last_id)[:batch_size]

        log.debug(
            'Batch %4d %4d %s  %s',
            loopidx, loopidx*batch_size, qs_s.model.__name__,
            last_id
        )

        yield qs_ss

        if qs_ss.count() < batch_size:
            # no more data
            break


def store_json_data(qs):
    """
    given store dataselectie json data
    """

    bulk = []

    for item in qs:

        bag_numid = item.locatie.bag_numid

        api_json = None
        uid = None

        try:
            if isinstance(item, models.Vestiging):
                api_json = serializers.VestigingDataselectie(item).data
                api_json['dataset'] = 'ves'
                uid = f'v{item.id}'

            elif isinstance(item, models.MaatschappelijkeActiviteit):
                api_json = (
                    serializers
                    .MaatschappelijkeActiviteitDataselectie(item)
                    .data
                )
                api_json['dataset'] = 'mac'
                uid = f'm{item.id}'
            else:
                raise ValueError('Unknown instance recieved..')

        except TypeError:
            log.exception('Could not save %s %s', uid, bag_numid)
            log.debug(f"""
                id: {item.id}
                bag: {bag_numid}
                bezoek: {item.bezoekadres.id} {item.bezoekadres.geometrie}
                post: {item.postadres.id} {item.postadres.geometrie}
            """)
            log.debug('SKIPPING')
            continue

        tracking['last_id'] = item.id

        bulk.append(
            models.DataSelectie(
                uid=uid,
                bag_numid=bag_numid,
                api_json=api_json,
            )
        )

    # Using bulk save to save on ORM handling
    # and db connections
    models.DataSelectie.objects.bulk_create(bulk)
    del bulk


def store_qs_data(full_qs):
    """
    Chunck queryset and only give relevant parts of chuncks to be
    indexed.

    This way we can devide the work up between workers
    """

    numerator = settings.PARTIAL_IMPORT['numerator']
    denominator = settings.PARTIAL_IMPORT['denominator']

    # reset id tracking
    tracking['last_id'] = None


    for qs_partial in generate_qs_parts(full_qs, denominator, numerator):
        store_json_data(qs_partial)


def write_dataselectie_data():
    """
    Writes dataselectie data to the database from the HR data

    The step parameter determings the size of each
    queryset to handle
    """

    # Deleting all previous data
    if settings.PARTIAL_IMPORT['denominator'] == 1:
        log.debug('DELETE')
        models.DataSelectie.objects.all().delete()

    store_qs_data(get_vestigingen())
    store_qs_data(get_maatschappelijke_activiteiten())
