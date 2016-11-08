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


class RandomShitTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.ves = factories.VestigingFactory()
        cls.mac = factories.MaatschappelijkeActiviteitFactory()

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

        for i in range(450):
            key_len = random.randint(1, 35)
            keylist = [random.choice(source) for i in range(key_len)]
            query = "".join(keylist)

            response = self.client.get(url, {
                'q': "".join(query)})

            self.assertEqual(response.status_code, 200)
