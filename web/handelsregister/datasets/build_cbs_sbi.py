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
        cursor.execute("""TRUNCATE TABLE hr_cbs_sbi_hoofdcat CASCADE""")

def _requestExec(req_parameter):
    data = None
    try:
        data = requests.get(req_parameter)
    except requests.ConnectionError:
        log.error("Connection Error")
    except requests.HTTPError:
        log.error("HTTPError")
    except requests.Timeout:
        log.error("Timeout")
    except requests.TooManyRedirects:
        log.error("TooManyRedirects")
    return data


def _fill_cbsbi_table():

    log.info("Vullen sbi codes vanuit cbs.typeermodule.typeerservicewebapi")
    code = 'start/0'
    vraag_url = settings.CBS_URI

    data = _requestExec(vraag_url.format(code))
    if data:
        _process_data_from_cbs(data, vraag_url)
        log.info("Vullen sbi codes voltooid")


def _process_data_from_cbs(data, vraag_url):
    for antwoord in data.json()['Answers']:
        hcat = CBS_sbi_hoofdcat(hcat=antwoord['Value'], hoofdcategorie=antwoord['Key'])
        hcat.save()

        next_url = vraag_url.format(antwoord['Value'])
        next_url += '/1'

        category_data = _requestExec(next_url)
        if category_data:

            _process_category_data(category_data, hcat)


def _process_category_data(category_data, hcat):
    # subantwoorden = category_data.json()['Answers']
    search_url = settings.CSB_SEARCH
    for sub_category_antwoord in category_data.json()['Answers']:

        # sub_cat = sub_category_antwoord['Key']
        # category_url_code = sub_category_antwoord['Value']
        scat = CBS_sbi_subcat(hcat=hcat, scat=sub_category_antwoord['Value'],
                              subcategorie=sub_category_antwoord['Key'])
        scat.save()

        search_url_k = search_url.format(sub_category_antwoord['Value'])
        category_codes = _requestExec(search_url_k)
        if category_codes:

            time.sleep(0.1)

            for item in category_codes.json():
                cbsbi = CBS_sbicodes(sbi_code=item['Code'],
                                     scat=scat,
                                     sub_sub_categorie=item['Title'])
                cbsbi.save()


def _check_download_complete():

    if CBS_sbi_hoofdcat.objects.count() == 0:
        from subprocess import call
        call('datasets/restore_cbs.sh')


def cbsbi_table():
    _clear_cbsbi_table()
    _fill_cbsbi_table()
    _check_download_complete()
