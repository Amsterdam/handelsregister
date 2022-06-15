
# django
from rest_framework.test import APITestCase

# Project
from datasets.hr.tests import factories as factories_hr
from datasets.hr import models as models_hr
from datasets.hr import improve_location_with_search
from .fixtures import patch_search_requests


@patch_search_requests
class CorrectBySearchTest(APITestCase):
    """Test the module that fixes incomplete location entries."""

    def setUp(self):
        """
        For x bag panden
        """
        self.locaties = factories_hr.create_search_test_locaties()

    def test_creation(self):
        """check if things are created"""
        self.assertEqual(3, models_hr.Locatie.objects.count())

    def test_invalid_count(self):
        """check if we can find invalid locations"""
        invalid = improve_location_with_search.create_qs_of_invalid_locations('Amsterdam')
        self.assertEqual(2, invalid.count())

        invalid = improve_location_with_search.create_qs_of_invalid_locations('Weesp')
        self.assertEqual(1, invalid.count())

    def test_completing(self):
        """Check if after guessing the is no more incomplete location."""

        for gemeente in ("Amsterdam", "Weesp"):
            invalid_adam = improve_location_with_search.create_qs_of_invalid_locations(gemeente)

            improve_location_with_search.guess()

            # check that all adresses have been seen and a correction attempt has been made
            self.assertEqual(0, invalid_adam.count())

            corrected = models_hr.Locatie.objects \
                .filter(geometrie__isnull=False) \
                .filter(volledig_adres__endswith=gemeente)

            # Check that 1 item should be corrected with toevoeging
            self.assertEqual(1, corrected.count())
