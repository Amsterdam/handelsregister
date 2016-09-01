import datetime
from decimal import Decimal

from django.test import TestCase

from datasets import build_hr_data
from datasets.kvkdump import models as kvk
from datasets.kvkdump import utils
from .. import models


class ImportPersoonTest(TestCase):
    def setUp(self):
        utils.generate_schema()

    def _convert(self, p: kvk.KvkPersoon) -> models.Persoon:
        build_hr_data.fill_stelselpedia()
        return models.Persoon.objects.get(pk=p.pk)

    def test_import_typical_example(self):
        p = kvk.KvkPersoon.objects.create(
            prsid=Decimal('100000000000000000'),
            prshibver=Decimal('100000000000000000')

            # ...
				    # datumuitschrijving='',
				    # datumuitspraak='',
				    # duur='',
				    # faillissement='',
				    # geboortedatum='',
				    # geboorteland='',
				    # geboorteplaats='',
				    # geemigreerd='',
				    # geheim='',
				    # geslachtsaanduiding='',
				    # geslachtsnaam='',
				    # handlichting='',
				    # huwelijksdatum='',
				    # naam='',
				    # nummer='',
				    # ookgenoemd='',
				    # persoonsrechtsvorm='',
				    # redeninsolvatie='',
				    # rsin='',
				    # soort='',
				    # status='',
				    # toegangscode='',
				    # typering='',
				    # uitgebreiderechtsvorm='',
				    # verkortenaam='',
				    # volledigenaam='',
				    # voornamen='',
				    # voorvoegselgeslachtsnaam='',
				    # prshibver='',
				    # rechtsvorm='',
				    # doelrechtsvorm='',
				    # rol=''
        )
        persoon = self._convert(p)

        self.assertIsNotNone(persoon)
				# ...
