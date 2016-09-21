from django.db import connection

from django.contrib.gis.geos import Point
from django.test import TestCase

from datasets.hr.tests import factories as hr_factories

from django.conf import settings

point = Point(0.0, 1.1)

URL = settings.DATAPUNT_API_URL


class ViewsTest(TestCase):

    def get_row(self, view_name):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM " + str(view_name) + " LIMIT 1")
        result = cursor.fetchone()
        self.assertIsNotNone(result)

        return dict(zip([col[0] for col in cursor.description], result))

    def test_vestiging_locaties(self):
        l = hr_factories.LocatieFactory.create(geometry=point)
        a1 = hr_factories.Activiteit.create()
        a2 = hr_factories.Activiteit.create()
        v = hr_factories.VestigingFactory.create(
            bezoekadres=l,
            activiteiten=[a1, a2],
            vestigingsnummer=99
        )

        row = self.get_row('geo_hr_vestiging_locaties')

        self.assertIn("geometrie", row)

        self.assertEqual(
            row['uri'],
            '{}handelsregister/vestiging/{}/'.format(URL, v.vestigingsnummer))
