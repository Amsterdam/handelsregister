from django.db import connection

from django.contrib.gis.geos import Point
from django.test import TestCase

from datasets import build_hr_data

from datasets.hr import models
from datasets.hr.tests import factories as hr_factories
from datasets.sbicodes import load_sbi_codes

from django.conf import settings


point = Point(0.0, 1.1)

URL = settings.DATAPUNT_API_URL


class ViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_sbi_codes.build_all_sbi_code_trees()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def get_row(self, view_name):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM " + str(view_name) + " LIMIT 1")
        result = cursor.fetchone()
        self.assertIsNotNone(result)

        return dict(zip([col[0] for col in cursor.description], result))

    def test_vestiging_locaties(self):
        l = hr_factories.LocatieFactory.create(geometrie=point)
        # hr_factories.SBIcatFactory.create()
        a1 = hr_factories.Activiteit.create(id='987')
        a2 = hr_factories.Activiteit.create(id='986')

        v = hr_factories.VestigingFactory.create(
            bezoekadres=l,
            activiteiten=[a1, a2],
            vestigingsnummer=99
        )

        build_hr_data.fill_geo_table()

        row = self.get_row('geo_hr_vestiging_locaties')

        self.assertIn("geometrie", row)

        self.assertEqual(
            row['uri'],
            '{}handelsregister/vestiging/{}/'.format(URL, v.vestigingsnummer))

    def test_existing_extra_sbi_geo_views(self):

        views = [
            "geo_hr_vestiging_locaties_overige",
            "geo_hr_vestiging_locaties_overige_naam",

            "geo_hr_vestiging_locaties_informatie_telecommunicatie",
            "geo_hr_vestiging_locaties_informatie_telecommunicatie_naam",

            "geo_hr_vestiging_locaties_persoonlijke_dienstverlening_naam",
            "geo_hr_vestiging_locaties_persoonlijke_dienstverlening",

            "geo_hr_vestiging_locaties_landbouw_naam",
            "geo_hr_vestiging_locaties_landbouw",

            "geo_hr_vestiging_locaties_handel_vervoer_opslag_naam",
            "geo_hr_vestiging_locaties_handel_vervoer_opslag",

            "geo_hr_vestiging_locaties_zakelijke_dienstverlening_naam",
            "geo_hr_vestiging_locaties_zakelijke_dienstverlening",

            "geo_hr_vestiging_locaties_productie_installatie_reparatie_naam",

            "geo_hr_vestiging_locaties",
            "geo_hr_vestiging_locaties_naam",

            "geo_hr_vestiging_locaties_bouw_naam",
            "geo_hr_vestiging_locaties_bouw",

            "geo_hr_vestiging_locaties_horeca",
            "geo_hr_vestiging_locaties_horeca_naam",

            # not the "na" because of max length
            "geo_hr_vestiging_locaties_financiele_dienstverlening_verhuur",
            "geo_hr_vestiging_locaties_financiele_dienstverlening_verhuur_na",

            "geo_hr_vestiging_locaties_cultuur_sport_recreatie",
            "geo_hr_vestiging_locaties_cultuur_sport_recreatie_naam",

            "geo_hr_vestiging_locaties_zakelijke_dienstverlening",
            "geo_hr_vestiging_locaties_zakelijke_dienstverlening_naam",

            "geo_hr_vestiging_locaties_productie_installatie_reparatie",
            "geo_hr_vestiging_locaties_productie_installatie_reparatie_naam",

            "geo_hr_vestiging_locaties_overheid_onderwijs_zorg",
            "geo_hr_vestiging_locaties_overheid_onderwijs_zorg_naam",
        ]

        for view_name in views:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT id, geometrie, naam, locatie_type
                FROM {} LIMIT 1
                """.format(str(view_name)))
            cursor.fetchone()

    def test_more_locaties(self):

        vestigingen = hr_factories.create_x_vestigingen()

        build_hr_data.fill_geo_table()

        # vestigingen hebben een post en een bezoek adres
        # dus 2 * de entries in de geo_table
        self.assertEqual(
            2 * len(vestigingen),
            models.GeoVestigingen.objects.all().count())

        post_count = (models.GeoVestigingen
                      .objects.filter(locatie_type='P').count())

        bezoek_count = (models.GeoVestigingen
                        .objects.filter(locatie_type='B').count())
        self.assertEqual(post_count, bezoek_count)
