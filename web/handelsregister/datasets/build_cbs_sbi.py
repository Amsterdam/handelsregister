"""
Slurp alle categorien en subcategorien van de cbs website af om met deze code's
de goede geo data tabel te kunnen maken.
"""

import logging
from django import db
from django.conf import settings
import requests
import json
import time
from datasets.hr.models import CBS_sbicodes, CBS_sbi_hoofdcat, CBS_sbi_subcat
log = logging.getLogger(__name__)


def _clear_cbsbi_table():

    log.info("Leegmaken oude cbs sbi codes")

    with db.connection.cursor() as cursor:
        cursor.execute("""TRUNCATE TABLE hr_cbs_sbi_hoofdcat CASCADE""")


def _request_exec(req_parameter):
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

    data = _request_exec(vraag_url.format(code))
    if data:
        _process_data_from_cbs(data, vraag_url)
        log.info("Vullen sbi codes voltooid")


def _process_data_from_cbs(data, vraag_url):
    for antwoord in data.json()['Answers']:
        hcat = CBS_sbi_hoofdcat(hcat=antwoord['Value'], hoofdcategorie=antwoord['Key'])
        hcat.save()

        next_url = vraag_url.format(antwoord['Value'])
        next_url += '/1'

        category_data = _request_exec(next_url)
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
        category_codes = _request_exec(search_url_k)
        if category_codes:

            time.sleep(0.1)

            for item in category_codes.json():
            # Met overige in horeca komen ook de andere categorieen mee!
            # Negeer daarom select op al aangemaakt!!
                if not item or CBS_sbicodes.objects.filter(sbi_code=item['Code']).count():
                    continue
                cbsbi = CBS_sbicodes(sbi_code=item['Code'],
                                     scat_id=scat.scat,
                                     sub_sub_categorie=item['Title'])
                cbsbi.save()


def _check_download_complete():

    if CBS_sbi_hoofdcat.objects.count() == 0:
        restore_cbs_sbi()


def restore_cbs_sbi():
    _restore_json('./datasets/kvkdump/fixture_files/hcat.json', CBS_sbi_hoofdcat, 'hcat')
    _restore_json('./datasets/kvkdump/fixture_files/scat.json', CBS_sbi_subcat, 'scat', 'hcat')
    _restore_json('./datasets/kvkdump/fixture_files/sbicodes.json', CBS_sbicodes, 'sbi_code', 'scat')


def _restore_json(filename, modelname, pkname='id', reference_field=None):
    with open(filename, 'r') as injson:
        indata = json.loads(injson.read())

    for rows in indata:
        newrow = modelname()
        for key, value in rows.items():
            if key == 'pk':
                setattr(newrow, pkname, value)
            elif key == 'fields':
                for fldname, fldvalue in value.items():
                    if fldname == reference_field:
                        fldname += '_id'
                    setattr(newrow, fldname, fldvalue)
        newrow.save()


def cbsbi_table():
    _clear_cbsbi_table()
    _fill_cbsbi_table()
    _check_download_complete()
