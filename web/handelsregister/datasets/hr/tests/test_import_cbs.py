from django.test import TestCase
from datasets import build_cbs_sbi
from ..models import CBS_sbi_hoofdcat, CBS_sbi_subcat, CBS_sbicodes

class ImportCSBTest(TestCase):

    def test_cbs_import(self):
        build_cbs_sbi._clear_cbsbi_table()

        build_cbs_sbi._fill_cbsbi_table()

        self.assertEqual(CBS_sbi_hoofdcat.objects.count(), 12)
        self.assertGreater(CBS_sbi_subcat.objects.count(), 12)
        self.assertGreater(CBS_sbicodes.objects.count(), 12)

