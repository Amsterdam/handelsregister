from django.test import TestCase
from django import db
from datasets import build_cbs_sbi
from ..models import CBS_sbi_hoofdcat, CBS_sbi_subcat, CBS_sbicodes


class ImportCSBTest(TestCase):

    def test_cbs_import(self):
        with db.connection.cursor() as cursor:
            try:
                cursor.execute("""drop table hr_cbs_sbicodes_save""")
                cursor.execute("""drop table hr_cbs_sbi_subcat_save""")
                cursor.execute("""drop table hr_cbs_sbi_hoofdcat_save""")
            except:
                cursor.execute("""rollback""")

        build_cbs_sbi._clear_cbsbi_table()

        build_cbs_sbi._fill_cbsbi_table()

        hoofdcatnr = CBS_sbi_hoofdcat.objects.count()
        subcatnr = CBS_sbi_subcat.objects.count()
        sbinr = CBS_sbicodes.objects.count()
        self.assertGreater(hoofdcatnr, 11)
        self.assertGreater(subcatnr, 12)
        self.assertGreater(sbinr, 12)

        build_cbs_sbi._clear_cbsbi_table()

        self.assertEqual(CBS_sbi_hoofdcat.objects.count(), 0)

        with db.connection.cursor() as cursor:
            cursor.execute("""select count(*) from hr_cbs_sbicodes_save""")
            r2 = cursor.fetchone()
            cursor.execute("""select count(*) from hr_cbs_sbi_subcat_save""")
            r1 = cursor.fetchone()
            cursor.execute("""select count(*) from hr_cbs_sbi_hoofdcat_save""")
            r0 = cursor.fetchone()
        self.assertEqual(r0[0], hoofdcatnr)
        self.assertEqual(r1[0], subcatnr)
        self.assertEqual(r2[0], sbinr)

        build_cbs_sbi._check_download_complete()
        self.assertEqual(CBS_sbi_hoofdcat.objects.count(), hoofdcatnr)
        self.assertEqual(CBS_sbi_subcat.objects.count(), subcatnr)
        self.assertEqual(CBS_sbicodes.objects.count(), sbinr)

