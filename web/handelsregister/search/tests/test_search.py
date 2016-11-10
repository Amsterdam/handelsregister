# Python
import json
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

        hnd1 = factories.Handelsnaam(handelsnaam='handelsnaam1')
        hnd11 = factories.Handelsnaam(handelsnaam='handelsnaam11')
        hnd2 = factories.Handelsnaam(handelsnaam='handelsnaam2')
        hnd3 = factories.Handelsnaam(handelsnaam='handelsnaam3')
        hnd_mac = factories.Handelsnaam(handelsnaam='mac_handelsnaam')

        onderneming = factories.Onderneming(handelsnamen=[hnd_mac])

        cls.mac1 = factories.MaatschappelijkeActiviteitFactory(
                naam='mac1',
                kvk_nummer='1111',
                onderneming=onderneming
        )

        cls.mac2 = factories.MaatschappelijkeActiviteitFactory(
                naam='mac2',
                kvk_nummer='0112'

        )
        cls.mac3 = factories.MaatschappelijkeActiviteitFactory(
                naam='mac3',
                kvk_nummer='0113'
        )

        cls.ves1 = factories.VestigingFactory(
                naam='test1',
                maatschappelijke_activiteit=cls.mac1,
                vestigingsnummer=99999,
                handelsnamen=[hnd1, hnd11]
        )
        cls.ves2 = factories.VestigingFactory(
                naam='test2',
                maatschappelijke_activiteit=cls.mac2,
                vestigingsnummer=99998,
                handelsnamen=[hnd2]
        )
        cls.ves3 = factories.VestigingFactory(
                naam='test3',
                maatschappelijke_activiteit=cls.mac3,
                vestigingsnummer=99988,
                handelsnamen=[hnd3]

        )

        build_index.reset_hr_docs()
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
            log.debug('random_testing: %s', url)
            self.bomb_endpoint(url)

    def bomb_endpoint(self, url):
        """
        Bomb enpoints with junk make sure nothing causes a
        crash
        """

        source = string.ascii_letters + string.digits + ' ' * 20

        for i in range(10):
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

        self.assertEqual(response.data['count'], 2)

        query = '0112'
        response = self.client.get(url, {'q': query})
        self.assertEqual(response.data['count'], 1)

        self.assertEqual(response.data['results'][0]['kvk_nummer'], '0112')

    def test_mac_naam(self):

        url = '/handelsregister/search/maatschappelijkeactiviteit/'
        query = 'mac'
        response = self.client.get(url, {'q': query})
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 3)

        query = 'mac3'
        response = self.client.get(url, {'q': query})

        self.assertEqual(response.data['results'][0]['naam'], 'mac3')

    def test_ves_id(self):

        url = '/handelsregister/search/vestiging/'
        query = 9999
        response = self.client.get(url, {'q': query})
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 2)

        query = 99998
        response = self.client.get(url, {'q': query})
        self.assertEqual(response.data['count'], 1)

        self.assertEqual(
            response.data['results'][0]['vestigingsnummer'], '99998')

    def test_ves_naam(self):

        url = '/handelsregister/search/vestiging/'
        query = 'test'
        response = self.client.get(url, {'q': query})
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 3)

        query = 'test3'
        response = self.client.get(url, {'q': query})

        # log.exception(json.dumps(response.data['results'], indent=2))

        self.assertEqual(
            response.data['results'][0]['naam'], 'test3')
