
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

    #    response = self.client.get(
    #        '/handelsregister/vestiging/?nummeraanduiding=0363010000758545')
    #    self.assertEquals(200, response.status_code)

    #def test_filter_vbo_id(self):
    #    response = self.client.get(
    #        '/handelsregister/vestiging/?verblijfsobject=0363010000758545')
    #    self.assertEquals(200, response.status_code)

    #def test_filter_pand_id(self):
    #    response = self.client.get(
    #        '/handelsregister/vestiging/?pand=0363010000758545')
    #    self.assertEquals(200, response.status_code)
    #    pass

    #def test_filter_kot_id(self):
    #    response = self.client.get(
    #        '/handelsregister/vestiging/?kadastraal_object=0363010000758545')
    #    self.assertEquals(200, response.status_code)
    #    pass

    #def test_unknown_vbo_is_404(self):
    #    response = self.client.get('/zwaailicht/status_pand/1234/')
    #    self.assertEquals(200, response.status_code)

    #def test_known_vbo_unknown_follow_is_200(self):
    #    response = self.client.get('/zwaailicht/status_pand/0363010001958552/')
    #    self.assertEquals(200, response.status_code)
