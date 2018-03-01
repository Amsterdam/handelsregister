# Packages
from rest_framework.test import APITestCase
# Project
from datasets.hr.tests import factories as factories_hr
# from datasets.sbicodes.tests import factories as factories_sbi
from datasets.sbicodes import load_sbi_codes

from . import authorization


class BrowseDatasetsTestCase(APITestCase, authorization.AuthorizationSetup):
    """
    Verifies that browsing the API works correctly.
    """

    datasets = [
        'handelsregister/maatschappelijkeactiviteit',
        'handelsregister/persoon',
        'handelsregister/vestiging',
        'handelsregister/functievervulling',
        'handelsregister/sbicodes',
    ]

    @classmethod
    def setUpClass(cls):
        load_sbi_codes.build_all_sbi_code_trees()
        super().setUpClass()

    def setUp(self):
        self.setUpAuthorization()
        a1 = factories_hr.Activiteit.create()
        a2 = factories_hr.Activiteit.create()

        mac = factories_hr.MaatschappelijkeActiviteitFactory.create(
            id=900000000000000000,
        )
        mac.activiteiten.set([a1, a2])

        factories_hr.PersoonFactory.create()
        factories_hr.VestigingFactory.create()
        factories_hr.FunctievervullingFactory.create()

    def test_index_pages(self):
        url = 'handelsregister'

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer {}'.format(self.token_scope_hr_r))
        response = self.client.get('/{}/'.format(url))

        self.assertEqual(
            response.status_code,
            200, 'Wrong response code for {}'.format(url))

    def valid_html_response(self, url, response):
        """
        Helper method to check common status/json
        """

        self.assertEqual(
            200, response.status_code,
            'Wrong response code for {}'.format(url))

        self.assertEqual(
            'text/html; charset=utf-8', response['Content-Type'],
            'Wrong Content-Type for {}'.format(url))

    def test_lists(self):
        for url in self.datasets:
            self.client.credentials(
                HTTP_AUTHORIZATION='Bearer {}'.format(self.token_scope_hr_r))
            response = self.client.get('/{}/'.format(url))

            self.assertEqual(
                response.status_code,
                200, 'Wrong response code for {}'.format(url))

            self.assertEqual(
                response['Content-Type'], 'application/json',
                'Wrong Content-Type for {}'.format(url))

            self.assertIn(
                'count', response.data, 'No count attribute in {}'.format(url))
            self.assertNotEqual(
                response.data['count'],
                0, 'Wrong result count for {}'.format(url))

    def test_lists_html(self):
        for url in self.datasets:
            self.client.credentials(
                HTTP_AUTHORIZATION='Bearer {}'.format(self.token_scope_hr_r))
            response = self.client.get('/{}/?format=api'.format(url))

            self.valid_html_response(url, response)

            self.assertIn(
                'count', response.data, 'No count attribute in {}'.format(url))
            self.assertNotEqual(
                response.data['count'],
                0, 'Wrong result count for {}'.format(url))

    def test_details(self):
        for url in self.datasets:
            self.client.credentials(
                HTTP_AUTHORIZATION='Bearer {}'.format(self.token_scope_hr_r))
            response = self.client.get('/{}/'.format(url))

            url = response.data['results'][0]['_links']['self']['href']
            detail = self.client.get(url)

            self.assertEqual(
                detail.status_code,
                200, 'Wrong response code for {}'.format(url))

            self.assertEqual(
                detail['Content-Type'],
                'application/json', 'Wrong Content-Type for {}'.format(url))

            self.assertIn('_display', detail.data)

    def test_details_html(self):
        for url in self.datasets:
            self.client.credentials(
                HTTP_AUTHORIZATION='Bearer {}'.format(self.token_scope_hr_r))
            response = self.client.get('/{}/?format=api'.format(url))

            url = response.data['results'][0]['_links']['self']['href']

            detail = self.client.get(url)

            self.valid_html_response(url, response)

            self.assertIn('_display', detail.data)
