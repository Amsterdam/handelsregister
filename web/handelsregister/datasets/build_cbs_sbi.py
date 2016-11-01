"""
Slurp alle categorien en subcategorien van de cbs website af om met deze code's
de goede geo data tabel te kunnen maken.
"""

import logging
from django import db
from django.conf import settings
import requests
import time
from datasets.hr.models import CBS_sbicodes, CBS_sbi_hoofdcat, CBS_sbi_subcat
log = logging.getLogger(__name__)


def _clear_cbsbi_table():

    log.info("Leegmaken oude cbs sbi codes")
    with db.connection.cursor() as cursor:
        cursor.execute("""TRUNCATE TABLE hr_CBS_sbicodes""")

def _fill_cbsbi_table():

    log.info("Vullen sbi codes vanuit cbs.typeermodule.typeerservicewebapi")
    code = 'start/0'
    vraag_url = settings.CBS_URI
    search_url = settings.CSB_SEARCH
    start_codes = {}

    data = requests.get(vraag_url.format(code))
    json_data = data.json()

    for antwoord in data.json()['Answers']:
        hcat = CBS_sbi_hoofdcat(hcat = antwoord['Value'], hoofdcategorie = antwoord['Key'])
        hcat.save()

        next_url = vraag_url.format(antwoord['Value'])
        next_url += '/1'

        category_data = requests.get(next_url)

        # subantwoorden = category_data.json()['Answers']
        for sub_category_antwoord in category_data.json()['Answers']:

            # sub_cat = sub_category_antwoord['Key']
            # category_url_code = sub_category_antwoord['Value']
            scat = CBS_sbi_subcat(hcat=hcat, scat=sub_category_antwoord['Value'], subcategorie=sub_category_antwoord['Key'])
            scat.save()

            search_url_k = search_url.format(sub_category_antwoord['Value'])
            category_codes = requests.get(search_url_k)

            time.sleep(0.1)

            for item in category_codes.json():
                cbsbi = CBS_sbicodes(sbi_code = item['Code'],
                                     scat = scat,
                                     sub_sub_categorie = item['Title'])
                cbsbi.save()

    log.info("Vullen sbi codes voltooid")


def cbsbi_table():
    _clear_cbsbi_table()
    _fill_cbsbi_table()
