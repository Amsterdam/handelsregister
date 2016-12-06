import rapidjson
from django.test import TestCase

from datasets import build_hr_data, build_ds_data
from datasets.hr import models
from datasets.hr.tests import factories as hr_factories
from rest_framework.test import APITestCase


class ImportDataselectieTest(TestCase):

    def get_row(self, key=None):
        if key:
            r = models.DataSelectie.objects.get(key)
            self.assertIsNotNone(r)
            return r

    def test_datasel_import(self):

        hr_factories.create_dataselectie_set()

        build_hr_data.fill_geo_table()

        build_ds_data._build_joined_ds_table()

        # this one is always there
        row = models.DataSelectie.objects.all()[0]
        self.assertIsNotNone(row)


        self.assertGreaterEqual(len(row.api_json), 1)
        self.assertEqual(len(row.api_json['bezoekadres']),11)
        self.assertIsInstance(row.api_json['sbi_codes'], list)
        self.assertEqual(len(row.api_json['sbi_codes']), 1)
        self.assertEqual(len(row.api_json['postadres']), 11)
        self.assertEqual(len(row.api_json['betrokkenen']), 1)
        self.assertIsInstance(row.api_json['geometrie'], list)
        self.assertEqual(row.api_json['postadres']['volledig_adres'][:9], 'vol_adres')
