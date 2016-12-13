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

        fields_in_row = ('geometrie', 'hoofdvestiging', 'kvk_nummer', 'locatie_type',
                         'naam', 'postadres_afgeschermd', 'postadres_correctie',
                         'postadres_huisletter', 'postadres_huisnummer',
                         'postadres_huisnummertoevoeging', 'postadres_postbus_nummer',
                         'postadres_postcode', 'postadres_straat_huisnummer',
                         'postadres_straatnaam', 'postadres_toevoegingadres',
                         'postadres_volledig_adres', 'sbi_codes', 'vestigingsnummer',
                         'datum_einde', 'datum_aanvang', 'bezoekadres_volledig_adres',
                         'bezoekadres_correctie', 'bezoekadres_afgeschermd',
                         'betrokkenen')

        for f in fields_in_row:
            self.assertIn(f, row.api_json)

        self.assertGreaterEqual(len(row.api_json), 1)
        self.assertIsInstance(row.api_json['sbi_codes'], list)
        self.assertEqual(len(row.api_json['sbi_codes']), 1)
        self.assertEqual(len(row.api_json['betrokkenen']), 1)
        self.assertIsInstance(row.api_json['geometrie'], list)
        self.assertEqual(row.api_json['postadres_volledig_adres'][:9], 'vol_adres')
