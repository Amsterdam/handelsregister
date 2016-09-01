
import logging

from django.conf import settings

from datasets.hr import doc as documents
from datasets.hr.models import MaatschappelijkeActiviteit

from datasets.elk import index


log = logging.getLogger(__name__)


HR_DOC_TYPES = [
    documents.MaatschappelijkeActiviteit
]


# TODO indexeer vestigingen

class DeleteMacIndex(index.DeleteIndexTask):
    index = settings.ELASTIC_INDICES['HR']
    doc_types = HR_DOC_TYPES


class MaatschappelijkIndexer(index.ImportIndexTask):
    name = "index maatschappelijke activiteit"

    queryset = MaatschappelijkeActiviteit.objects.\
        prefetch_related('postadres').\
        prefetch_related('bezoekadres').all()

    # prefetch_related('hoofdvestiging').\
    # prefetch_related('activiteiten').\
    # prefetch_related('eigenaar').\

    def convert(self, obj):
        return documents.from_mac(obj)


def index_mac_docs():
    DeleteMacIndex().execute()
    MaatschappelijkIndexer().execute()
