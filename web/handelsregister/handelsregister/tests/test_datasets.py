# Packages
from rest_framework.test import APITestCase
from unittest.mock import Mock
from django.http import HttpResponse
# Project
from datasets.hr.tests import factories as factories_hr


class BrowseDatasetsTestCase(APITestCase):
    """
    Verifies that browsing the API works correctly.
    """

    datasets = [
        'handelsregister/maatschappelijkeactiviteit',
        'handelsregister/persoon',
        'handelsregister/vestiging',
        'handelsregister/functievervulling',
    ]

    def setUp(self):
        factories_hr.MaatschappelijkeActiviteitFactory.create()
        factories_hr.PersoonFactory.create()
        factories_hr.VestigingFactory.create()
        factories_hr.FunctievervullingFactory.create()

    def test_lists(self):
        for url in self.datasets:
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

    def test_details(self):
        for url in self.datasets:
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
