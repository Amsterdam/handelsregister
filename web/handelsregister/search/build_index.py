
import logging

from django.conf import settings

from datasets.hr import doc as documents

from datasets.hr.models import MaatschappelijkeActiviteit
from datasets.hr.models import Vestiging

from search import index


log = logging.getLogger(__name__)


HR_DOC_TYPES = [
    documents.MaatschappelijkeActiviteit,
    documents.Vestiging
]


class ResetHRIndex(index.ResetIndexTask):
    index = settings.ELASTIC_INDICES['HR']
    doc_types = HR_DOC_TYPES


class MaatschappelijkIndexer(index.ImportIndexTask):
    name = "Index maatschappelijke activiteit"

    queryset = MaatschappelijkeActiviteit.objects.\
        prefetch_related('postadres').\
        prefetch_related('bezoekadres').order_by('id').all()

    def convert(self, obj):
        return documents.from_mac(obj)


class VestigingenIndexer(index.ImportIndexTask):
    name = "Index vestigingen"

    queryset = Vestiging.objects.\
        prefetch_related('postadres').\
        prefetch_related('bezoekadres').\
        prefetch_related('activiteiten').\
        order_by('id').all()

    def convert(self, obj):
        return documents.from_vestiging(obj)


def index_mac_docs():
    MaatschappelijkIndexer().execute()


def index_ves_docs():
    VestigingenIndexer().execute()


def reset_hr_docs():
    ResetHRIndex().execute()
