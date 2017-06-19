
from django.test import TestCase


class TestHealthStatus(TestCase):
    """
    Test health and status

    crucial for deployment
    """

    def test_status_health(self):
        """
        test health endpoint
        """
        url = 'status/health'

        response = self.client.get(f'/{url}')

        self.assertEqual(
            response.status_code,
            200, f'Wrong response code for {url} should be 200')

    def test_status_data(self):
        """
        test data endpoint
        """
        url = 'status/data'

        response = self.client.get(f'/{url}')

        self.assertEqual(
            response.status_code,
            500, f'Wrong response code for {url} should be 500')
