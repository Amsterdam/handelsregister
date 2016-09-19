
import random

# django
from rest_framework.test import APITestCase


# Project
from datasets.hr.tests import factories as factories_hr
from datasets.hr import models as models_hr
from .fixtures import patch_filter_requests


@patch_filter_requests
class VestingFilterTest(APITestCase):

    # create some factory stuff

    def setUp(self):
        """
        For x bag panden
        """

        self.vestigingen = []

        mac = factories_hr.MaatschappelijkeActiviteitFactory.create()

        for i in range(5):

            loc_b = factories_hr.LocatieFactory.create(
                    id='{}{}'.format('b', i),
                    bag_numid=i,
                    bag_vbid=i
            )
            loc_p = factories_hr.LocatieFactory.create(
                    id=i*100+1,
                    bag_numid='p{}'.format(i),
                    bag_vbid='p{}'.format(i)
            )

            for v in range(random.randint(0, 10)):
                ves = factories_hr.VestigingFactory.create(
                    id='{}-{}'.format(i, v),
                    bezoekadres=loc_b,
                    postadres=loc_p,
                    maatschappelijke_activiteit=mac
                )
                self.vestigingen.append(ves)

    def test_simple_response(self):
        """
        Verify that the endpoint exists.
        """
        test_id = self.vestigingen[0].vestigingsnummer

        response = self.client.get(
            '/handelsregister/vestiging/{}/'.format(test_id))

        self.assertEquals(200, response.status_code)

    def test_filter_nummeraanduiding(self):
        vestigingen = models_hr.Vestiging.objects.filter(
           bezoekadres__bag_numid=0,
        )
        vestigingen_p = models_hr.Vestiging.objects.filter(
           postadres__bag_numid='p0',
        )

        response_b = self.client.get(
            '/handelsregister/vestiging/?nummeraanduiding=0')

        data_b = response_b.json()
        self.assertEquals(200, response_b.status_code)
        self.assertEquals(vestigingen.count(), data_b['count'])

        response_p = self.client.get(
            '/handelsregister/vestiging/?nummeraanduiding=p0')

        data_p = response_p.json()

        self.assertEquals(200, response_p.status_code)
        self.assertEquals(vestigingen_p.count(), data_p['count'])

    def test_filter_vbo_id(self):

        vestigingen = models_hr.Vestiging.objects.filter(
           bezoekadres__bag_vbid=5,
        )

        response = self.client.get(
            '/handelsregister/vestiging/?verblijfsobject=0363010000758545')

        data = response.json()
        self.assertEquals(200, response.status_code)

        self.assertEquals(vestigingen.count(), data['count'])

    def test_filter_pand_id(self):
        """
        We mock the bag api endpoint request with json fixtures
        """

        # json contains verblijsfsobjecten with id 4 for given
        # pand id
        vestigingen = models_hr.Vestiging.objects.filter(
           bezoekadres__bag_numid=4,
        )

        response = self.client.get(
            '/handelsregister/vestiging/?pand=0363010000758545')

        self.assertEquals(200, response.status_code)
        data = response.json()

        self.assertEquals(vestigingen.count(), data['count'])

    def test_filter_kot_id(self):
        """
        """
        #
        vestigingen = models_hr.Vestiging.objects.filter(
           bezoekadres__bag_numid__in=[1, 2, 'p1'],
        )

        vestigingen_to_few = models_hr.Vestiging.objects.filter(
           bezoekadres__bag_numid__in=['p1'],
        )

        response = self.client.get(
            '/handelsregister/vestiging/?kadastraal_object=NL.KAD.OnroerendeZaak.11450749270000')
        self.assertEquals(200, response.status_code)

        data = response.json()

        print(data['count'])

        self.assertEquals(vestigingen.count(), data['count'])
        self.assertNotEqual(vestigingen_to_few.count(), data['count'])

    def test_unknown_vbo_is_200(self):
        """
        """
        response = self.client.get(
            '/handelsregister/vestiging/?verblijfsobject=9999')

        self.assertEquals(200, response.status_code)
