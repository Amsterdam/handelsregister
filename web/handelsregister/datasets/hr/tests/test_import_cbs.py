from rest_framework.test import APITestCase
from django import db
from datasets import build_cbs_sbi
from ..models import CBS_sbi_endcode, CBS_sbi_hoofdcat, CBS_sbi_subcat, \
                     CBS_sbi_section, CBS_sbi_rootnode, CBS_sbicode

from .fixtures import patch_cbs_requests


@patch_cbs_requests
class ImportCSBTest(APITestCase):

    def test_cbs_import(self):

        build_cbs_sbi._clear_cbsbi_table()
        self.assertEqual(CBS_sbi_section.objects.count(), 0)
        self.assertEqual(CBS_sbi_hoofdcat.objects.count(), 0)

        build_cbs_sbi._fill_cbsbi_table()

        hoofdcatnr = CBS_sbi_hoofdcat.objects.count()
        subcatnr = CBS_sbi_subcat.objects.count()
        sbi_endcode_nr = CBS_sbi_endcode.objects.count()
        self.assertEqual(hoofdcatnr, 12)
        self.assertEqual(subcatnr, 7)
        self.assertEqual(sbi_endcode_nr, 10)

        sections_nr = CBS_sbi_section.objects.count()
        rootnodes_nr = CBS_sbi_rootnode.objects.count()
        sbi_codes_nr = CBS_sbicode.objects.count()
        self.assertEqual(sections_nr, 1)
        self.assertEqual(rootnodes_nr, 3)
        self.assertEqual(sbi_codes_nr, 132)

        with db.connection.cursor() as cursor:
            cursor.execute("""COMMIT""")

        self.assertEqual(
            0, len(CBS_sbi_endcode.objects.filter(sbi_code='0113')))
        self.assertEqual(
            0, len(CBS_sbi_endcode.objects.filter(sbi_code='113')))
        self.assertEqual(
            1, len(CBS_sbicode.objects.filter(sbi_code='0113')))
        self.assertEqual(
            1, len(CBS_sbicode.objects.filter(sbi_code='113')))

        node = CBS_sbicode.objects.filter(sbi_code='113')[0]

        self.assertEqual(node.sub_cat.subcategorie, 'teelt eenjarige gewassen')

        build_cbs_sbi._clear_cbsbi_table()
        self.assertEqual(CBS_sbi_section.objects.count(), 0)
        self.assertEqual(CBS_sbi_hoofdcat.objects.count(), 0)
