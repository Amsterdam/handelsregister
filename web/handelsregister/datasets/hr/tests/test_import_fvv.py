import datetime
from decimal import Decimal

from django.test import TestCase

from datasets import build_hr_data
from datasets.kvkdump import models as kvk
from datasets.kvkdump import utils
from .. import models


class ImportFunctievervullingTest(TestCase):
    def setUp(self):
        utils.generate_schema()

    def _convert(self, fvv: kvk.KvkFunctievervulling) -> models.Functievervulling:
        build_hr_data.fill_stelselpedia()
        return models.Functievervulling.objects.get(pk=fvv.pk)

    def test_import_typical_example(self):
        fvv = kvk.KvkFunctievervulling.objects.create(
            ashid=Decimal('100000000000000000'),
            functie="GrandPoobah",
            prsidi=Decimal('200000000000000000'),
            prsidh=Decimal('300000000000000000'),
            soort="OnbeperktBevoegd",
            prsashhibver=Decimal('100000000000000000'),
        )
        functievervulling = self._convert(fvv)

        self.assertIsNotNone(functievervulling)
        self.assertEqual('100000000000000000', functievervulling.id)
        self.assertEqual('GrandPoobah', functievervulling.functietitel)
        self.assertEqual('OnbeperktBevoegd', functievervulling.soortbevoegdheid)
        self.assertEqual(Decimal('300000000000000000'), functievervulling.heeft_aansprakelijke_id)
        self.assertEqual(Decimal('200000000000000000'), functievervulling.is_aansprakelijke_id)
