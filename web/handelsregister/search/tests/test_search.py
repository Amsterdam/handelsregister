# Python
import string
import random
# Packages
from rest_framework.test import APITestCase
from datasets.hr.tests import factories
# Project

from search import build_index

import logging

log = logging.getLogger(__name__)


class SearchTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.mac1 = factories.MaatschappelijkeActiviteitFactory(
                naam='mac_1',
                kvk_nummer='1111'

        )

        cls.mac2 = factories.MaatschappelijkeActiviteitFactory(
                naam='mac_2',
                kvk_nummer='0112'

        )
        cls.mac3 = factories.MaatschappelijkeActiviteitFactory(
                naam='mac_3',
                kvk_nummer='0113'
        )

        cls.ves1 = factories.VestigingFactory(
                naam='test1',
                vestigingsnummer=99999
        )
        cls.ves2 = factories.VestigingFactory(
                naam='test2',
                vestigingsnummer=99998
        )
        cls.ves3 = factories.VestigingFactory(
                naam='test3',
                vestigingsnummer=99988

        )

        build_index.index_mac_docs()
        build_index.index_ves_docs()

    def test_random_shit_endpoints(self):
        """
        random stuff that crashes search / inspired by smoke tests
        """
        search_endpoints = [
            '/handelsregister/typeahead/',
            '/handelsregister/search/vestiging/',
            '/handelsregister/search/maatschappelijkeactiviteit/',
        ]

        for url in search_endpoints:
            #log.debug('random_testing: %s', url)
            self.bomb_endpoint(url)

    def bomb_endpoint(self, url):
        """
        Bomb enpoints with junk make sure nothing causes a
        crash
        """

        source = string.ascii_letters + string.digits + ' ' * 20

        for i in range(155):
            key_len = random.randint(1, 35)
            keylist = [random.choice(source) for i in range(key_len)]
            query = "".join(keylist)

            response = self.client.get(url, {
                'q': "".join(query)})

            self.assertEqual(response.status_code, 200)

    def test_mac_kvk(self):

        url = '/handelsregister/search/maatschappelijkeactiviteit/'
        query = '011'
        response = self.client.get(url, {'q': query})
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)

        #log.exception(response.data['results'])
        #self.assertEqual(response.data['count'], 2)

        query = '0112'
        response = self.client.get(url, {'q': query})
        #self.assertEqual(response.data['count'], 1)

        #self.assertEqual(response.data['results'][0]['kvk_nummer'], '0112')

    def test_mac_naam(self):

        url = '/handelsregister/search/maatschappelijkeactiviteit/'
        query = 'mac'
        response = self.client.get(url, {'q': query})
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        #log.exception(response.data['results'])
        #self.assertEqual(response.data['count'], 3)

        query = 'mac_3'
        response = self.client.get(url, {'q': query})
        #self.assertEqual(response.data['count'], 1)

        #self.assertEqual(response.data['results'][0]['naam'], 'mac_3')

    def test_ves_id(self):

        url = '/handelsregister/search/vestiging/'
        query = 9999
        response = self.client.get(url, {'q': query})
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        #self.assertEqual(response.data['count'], 2)

        query = 99998
        response = self.client.get(url, {'q': query})
        #self.assertEqual(response.data['count'], 1)

        #self.assertEqual(
            #response.data['results'][0]['vestigingsnummer'], '99998')

    def test_ves_naam(self):

        url = '/handelsregister/search/vestiging/'
        query = 'test'
        response = self.client.get(url, {'q': query})
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        #self.assertEqual(response.data['count'], 3)

        query = 'test3'
        response = self.client.get(url, {'q': query})
        #self.assertEqual(response.data['count'], 1)

        #self.assertEqual(
        #    response.data['results'][0]['naam'], 'test3')
