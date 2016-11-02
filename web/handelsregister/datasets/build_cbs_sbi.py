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

    _delete_save_tables()

    with db.connection.cursor() as cursor:
        cursor.execute("""CREATE TABLE hr_cbs_sbi_hoofdcat_save AS select * from hr_cbs_sbi_hoofdcat""")
        cursor.execute("""CREATE TABLE hr_cbs_sbi_subcat_save AS select * from hr_cbs_sbi_subcat""")
        cursor.execute("""CREATE TABLE hr_cbs_sbicodes_save AS select * from hr_cbs_sbicodes""")

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
    search_url = settings.CSB_SEARCH

    data = _requestExec(vraag_url.format(code))
    if data:
        for antwoord in data.json()['Answers']:
            hcat = CBS_sbi_hoofdcat(hcat=antwoord['Value'], hoofdcategorie=antwoord['Key'])
            hcat.save()

            next_url = vraag_url.format(antwoord['Value'])
            next_url += '/1'

            category_data = _requestExec(next_url)
            if category_data:

                # subantwoorden = category_data.json()['Answers']
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

        log.info("Vullen sbi codes voltooid")


def _delete_save_tables():
    with db.connection.cursor() as cursor:
        try:
            cursor.execute("""Drop table hr_cbs_sbi_hoofdcat_save""")
            cursor.execute("""Drop table hr_cbs_sbi_subcat_save""")
            cursor.execute("""Drop table hr_cbs_sbicodes_save""")
        except:
            cursor.execute("""rollback""")


def _check_download_complete():

    with db.connection.cursor() as cursor:
        cursor.execute("""select count(*) from hr_cbs_sbi_hoofdcat""")
        r_new = cursor.fetchone()
        if r_new[0] == 0:
            log.error("Nieuwe download van sbicodes is leeg, oude waarden worden teruggezet!")
            cursor.execute("""TRUNCATE TABLE hr_cbs_sbi_hoofdcat CASCADE""")
            cursor.execute("""INSERT INTO hr_cbs_sbi_hoofdcat SELECT * from hr_cbs_sbi_hoofdcat_save""")
            cursor.execute("""INSERT INTO hr_cbs_sbi_subcat SELECT * from hr_cbs_sbi_subcat_save""")
            cursor.execute("""INSERT INTO hr_cbs_sbicodes SELECT * from hr_cbs_sbicodes_save""")

    _delete_save_tables()


def cbsbi_table():
    _clear_cbsbi_table()
    _fill_cbsbi_table()
    _check_download_complete()
