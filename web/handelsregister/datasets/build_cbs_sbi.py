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
    section_data = _request_exec(settings.CBS_SECTIONS_URI)

    if section_data:
        _process_sectiondata_from_cbs(section_data)
        log.info("Vullen alle sbi codes voltooid")


def _process_sectiondata_from_cbs(section_data):
    for section in section_data.json():
        hcat = CBS_sbi_hoofdcat(hcat=section['Letter'], hoofdcategorie=section['Title'])
        hcat.save()

        _process_section(hcat)


def _process_section(hcat):
    section_tree_data_url = settings.CBS_SECTIONSTREE_URI.format(hcat.hcat)
    section_tree_data = _request_exec(section_tree_data_url)

    if section_tree_data:
        _process_sectiondatatree(section_tree_data, hcat)
        log.info("Vullen sbi codes sectie {} voltooid".format(hcat.hcat))


def _process_sectiondatatree(section_tree_data, hcat):
    section_tree = section_tree_data.json()

    subcat_set = {}
    for subcat in [node for node in section_tree if node['IsRoot']]:
        scat = CBS_sbi_subcat(hcat=hcat, scat=subcat['Code'], subcategorie=subcat['Title'])
        scat.save()
        subcat_set[subcat['Code']] = scat

    for sbi_code in [node for node in section_tree if not node['IsRoot']]:
        scat_code = sbi_code['Code'][:2]
        cbsbi = CBS_sbicodes(sbi_code=sbi_code['Code'],
                             scat=subcat_set[scat_code],
                             sub_sub_categorie=sbi_code['Title'])
        cbsbi.save()


def _check_download_complete():

    if CBS_sbi_hoofdcat.objects.count() == 0:
        restore_cbs_sbi()


def restore_cbs_sbi():
    _restore_json(
        './datasets/kvkdump/fixture_files/hcat.json',
        CBS_sbi_hoofdcat, 'hcat')
    _restore_json(
        './datasets/kvkdump/fixture_files/scat.json',
        CBS_sbi_subcat, 'scat', 'hcat')
    _restore_json(
        './datasets/kvkdump/fixture_files/sbicodes.json',
        CBS_sbicodes, 'sbi_code', 'scat')


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
