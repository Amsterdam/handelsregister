from django.test import TestCase
from django import db
from datasets import build_cbs_sbi
from ..models import CBS_sbi_hoofdcat, CBS_sbi_subcat, CBS_sbicodes


class ImportCSBTest(TestCase):

    def test_cbs_import(self):

        build_cbs_sbi._clear_cbsbi_table()

        build_cbs_sbi._fill_cbsbi_table()

        hoofdcatnr = CBS_sbi_hoofdcat.objects.count()
        subcatnr = CBS_sbi_subcat.objects.count()
        sbinr = CBS_sbicodes.objects.count()
        self.assertGreater(hoofdcatnr, 11)
        self.assertGreater(subcatnr, 12)
        self.assertGreater(sbinr, 12)

        with db.connection.cursor() as cursor:
            cursor.execute("""COMMIT""")

        build_cbs_sbi._clear_cbsbi_table()

        self.assertEqual(CBS_sbi_hoofdcat.objects.count(), 0)

        build_cbs_sbi._check_download_complete()
        self.assertGreater(CBS_sbi_hoofdcat.objects.count(), 11)
        self.assertGreater(CBS_sbi_subcat.objects.count(), 12)
        self.assertGreater(CBS_sbicodes.objects.count(), 12)

