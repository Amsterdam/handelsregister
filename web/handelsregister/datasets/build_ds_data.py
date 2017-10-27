import logging

from django.conf import settings

from datasets.hr import models, serializers

log = logging.getLogger(__name__)


def get_vestigingen(
        offset: int = 0, size: int = None) -> object:
    """
    Generates a query set to build json data for dataselectie
    An optional offset and size parameters can be given to limit
    the size of the queryset
    """
    qs = models.Vestiging.objects \
        .select_related('maatschappelijke_activiteit') \
        .select_related('maatschappelijke_activiteit__eigenaar') \
        .select_related('bezoekadres') \
        .select_related('postadres') \
        .prefetch_related('activiteiten') \
        .prefetch_related('activiteiten__sbi_code_tree') \
        .prefetch_related('handelsnamen') \
        .filter(datum_einde__isnull=True) \
        .order_by('id')

    if size:
        qs = qs[offset:size]
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
        .prefetch_related('communicatiegegevens')
    )

    qs_p = (
        qs.filter(bezoekadres__plaats='Amsterdam')
    )
    qs_b = (
        qs.filter(postadres__plaats='Amsterdam')
    )

    return qs_p | qs_b


def chunck_qs_by_id(qs, chuncks=1000):
    """
    Determine ID range, chunck up range.
    """
    if not qs.count():
        return []

    min_id = int(qs.first().id)
    max_id = int(qs.last().id)

    delta_step = int((max_id - min_id) / chuncks) or 1

    log.debug(
        'id range %s %s, chunksize %s', min_id, max_id, delta_step)

    steps = list(range(min_id, max_id, delta_step))
    # add max id range (bigger then last_id)
    steps.append(max_id+1)
    return steps


def return_qs_parts(qs, modulo, modulo_value):
    """ generate qs within min_id and max_id

        modulo and modulo_value determin which chuncks
        are teturned.

        if partial = 1/3

        then this function only returns chuncks index i for which
        modulo i % 3 == 1
    """

    steps = chunck_qs_by_id(qs, 1000)

    for i in range(len(steps)-1):
        if not i % modulo == modulo_value:
            continue
        start_id = steps[i]
        end_id = steps[i+1]
        qs_s = qs.filter(id__gte=start_id).filter(id__lt=end_id)
        log.debug('Count: %s range %s %s', qs_s.count(), start_id, end_id)
        yield qs_s


def store_json_data(qs):
    """
    given store dataselectie json data
    """

    bulk = []
    for item in qs:
        bag_numid = item.locatie.bag_numid

        api_json = None
        uid = None

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


def store_qs_data(full_qs):
    """
    Chunck queryset and only give relevant parts of chuncks to be
    indexed.

    This way we can devide the work up between workers
    """

    numerator = settings.PARTIAL_IMPORT['numerator']
    denominator = settings.PARTIAL_IMPORT['denominator']

    total = full_qs.count()

    sumcount = 0

    for qs_partial in return_qs_parts(full_qs, denominator, numerator):
        p_count = qs_partial.count()
        sumcount += p_count
        store_json_data(qs_partial)

    log.debug('%s %s', total, sumcount)
    return sumcount


def write_dataselectie_data():
    """
    Writes dataselectie data to the database from the HR data

    The step parameter determings the size of each
    queryset to handle
    """
    # Deleting all previous data
    if settings.PARTIAL_IMPORT['denominator'] == 1:
        models.DataSelectie.objects.all().delete()

    store_qs_data(get_vestigingen())
    store_qs_data(get_maatschappelijke_activiteiten())
