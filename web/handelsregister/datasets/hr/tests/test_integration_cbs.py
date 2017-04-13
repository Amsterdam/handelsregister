import logging
from rest_framework.test import APITestCase
from datasets import build_cbs_sbi
from ..models import CBS_sbi_endcode, CBS_sbi_hoofdcat, CBS_sbi_subcat, \
    CBS_sbi_section, CBS_sbi_rootnode, CBS_sbicode

from unittest import skip


log = logging.getLogger(__name__)


class ImportCSBIntegrationTest(APITestCase):

    @skip("Needs internet")
    def test_live_cbs_import(self):

        build_cbs_sbi._clear_cbsbi_table()
        self.assertEqual(CBS_sbi_section.objects.count(), 0)
        self.assertEqual(CBS_sbi_hoofdcat.objects.count(), 0)

        build_cbs_sbi._fill_cbsbi_table()

        self.assertGreater(CBS_sbi_hoofdcat.objects.count(), 10)
        self.assertGreater(CBS_sbi_subcat.objects.count(), 20)
        self.assertGreater(CBS_sbi_endcode.objects.count(), 500)

        self.assertGreater(CBS_sbi_section.objects.count(), 15)
        self.assertGreater(CBS_sbi_rootnode.objects.count(), 75)
        self.assertGreater(CBS_sbicode.objects.count(), 500)
