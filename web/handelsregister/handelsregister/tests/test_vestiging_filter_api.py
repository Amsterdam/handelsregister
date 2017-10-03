
import logging

# django
from rest_framework.test import APITestCase

# Project
from datasets.hr.tests import factories as factories_hr
from datasets.hr import models as models_hr
from .fixtures import patch_filter_requests
from . import authorization

LOG = logging.getLogger(__name__)


@patch_filter_requests
class VestingFilterTest(APITestCase, authorization.AuthorizationSetup):

    # create some factory stuff

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vestigingen = factories_hr.create_x_vestigingen()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        """
        For x bag panden
        """
        self.setUpAuthorization()
        # factories_hr.restore_cbs_sbi()

    def test_simple_response(self):
        """
        Verify that the endpoint exists.
        """
        test_id = self.vestigingen[0].vestigingsnummer

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {}'.format(self.token_employee))
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

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {}'.format(self.token_employee))
        response_b = self.client.get(
            '/handelsregister/vestiging/?nummeraanduiding=0')

        data_b = response_b.json()
        self.assertEquals(200, response_b.status_code)
        self.assertEquals(vestigingen.count(), data_b['count'])

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {}'.format(self.token_employee))
        response_p = self.client.get(
            '/handelsregister/vestiging/?nummeraanduiding=p0')

        data_p = response_p.json()

        self.assertEquals(200, response_p.status_code)
        self.assertEquals(vestigingen_p.count(), data_p['count'])

    def test_filter_vbo_id(self):

        vestigingen = models_hr.Vestiging.objects.filter(
           bezoekadres__bag_vbid=5,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {}'.format(self.token_employee))

        response = self.client.get(
            '/handelsregister/vestiging/?verblijfsobject=5')

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

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {}'.format(self.token_employee))
        response = self.client.get(
            '/handelsregister/vestiging/?pand=0363010000758545')

        self.assertEquals(200, response.status_code)
        data = response.json()

        self.assertEquals(vestigingen.count(), data['count'])

    def test_filter_kot_id(self):
        """
        We created some vbo's in setup using fixtures
        The vbo's we can now find/filter in the fixtures
        A reqest for vbo's id's is done to kot api in the filter.
        The returend id's should be found
        """
        # vestigingen filter which should be in fixture response
        # of kot. minimal 3 max 30
        vestigingen = models_hr.Vestiging.objects.filter(
           bezoekadres__bag_numid__in=[1, 2, 'p1']
        )

        # minimal 1 max 10
        vestigingen_to_few = models_hr.Vestiging.objects.filter(
           bezoekadres__bag_numid__in=['p1']
        )

        # Trigger a filter request with kot object id
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {}'.format(self.token_employee))
        response = self.client.get(
            '/handelsregister/vestiging/?kadastraal_object=NL.KAD.OnroerendeZaak.11450749270000')

        self.assertEquals(200, response.status_code)

        data = response.json()

        # We should be able to find all vestigingen
        # using 1, 2 and p1 location
        self.assertEquals(vestigingen.count(), data['count'])
        self.assertNotEqual(vestigingen_to_few.count(), data['count'])

    def test_unknown_vbo_is_200(self):
        """
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {}'.format(self.token_employee))
        response = self.client.get(
            '/handelsregister/vestiging/?verblijfsobject=9999')

        self.assertEquals(200, response.status_code)

    def test_dataselectie_filter(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {}'.format(self.token_employee))
        response = self.client.get(
            '/handelsregister/dataselectie/?sbi_code=1073')
