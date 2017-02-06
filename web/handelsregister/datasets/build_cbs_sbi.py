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
from datasets.hr.models import CBS_sbi_endcode, CBS_sbi_hoofdcat, CBS_sbi_subcat, \
                               CBS_sbi_section, CBS_sbi_rootnode, CBS_sbicode

log = logging.getLogger(__name__)


def _clear_cbsbi_table():

    log.info("Leegmaken oude cbs sbi codes")

    with db.connection.cursor() as cursor:
        cursor.execute("""TRUNCATE TABLE hr_cbs_sbi_section CASCADE""")
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
    log.info("Vullen sbi endcodes vanuit cbs.typeermodule.typeerservicewebapi")
    code = 'start/0'
    vraag_url = settings.CBS_URI

    data = _request_exec(vraag_url.format(code))
    if data:
        _process_data_from_cbs(data, vraag_url)
        _fill_complete_cbsbi_tables()
        log.info("Vullen sbi endcodes voltooid")


def _process_data_from_cbs(data, vraag_url):
    for antwoord in data.json()['Answers']:
        hcat = CBS_sbi_hoofdcat(
            hcat=antwoord['Value'], hoofdcategorie=antwoord['Key'])
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
                if not item or CBS_sbi_endcode.objects.filter(
                        sbi_code=item['Code']).count():
                    continue
                cbsbi = CBS_sbi_endcode(sbi_code=item['Code'],
                                        scat_id=scat.scat,
                                        sub_sub_categorie=item['Title'])
                cbsbi.save()


def _fill_complete_cbsbi_tables():
    # add a fallback for missing codes
    fallback_hoofd = CBS_sbi_hoofdcat.objects.filter(hoofdcategorie='overige niet hierboven genoemd')[0]
    fallback = CBS_sbi_subcat(scat="XXX", subcategorie="ongeplaatst", hcat=fallback_hoofd)
    fallback.save()

    log.info("Vullen complete sbi codes vanuit cbs.typeermodule.typeerservicewebapi")
    section_data = _request_exec(settings.CBS_SECTIONS_URI)
    if section_data:
        _process_sectiondata_from_cbs(section_data)
        log.info("Vullen alle sbi codes voltooid")


def _process_sectiondata_from_cbs(section_data):
    for section in section_data.json():
        section = CBS_sbi_section(code=section['Letter'], title=section['Title'])
        section.save()

        _process_section(section)


def _process_section(section):
    section_tree_data_url = settings.CBS_SECTIONSTREE_URI.format(section.code)
    section_tree_data = _request_exec(section_tree_data_url)

    if section_tree_data:
        _process_sectiondatatree(section_tree_data, section)
        log.info("Vullen sbi codes sectie {} voltooid".format(section.code))


def _process_sectiondatatree(section_tree_data, section):
    section_tree = section_tree_data.json()

    rootnode_set = {}
    for node in [node for node in section_tree if node['IsRoot']]:
        rootnode = CBS_sbi_rootnode(section=section, code=node['Code'], title=node['Title'])
        rootnode.save()
        rootnode_set[node['Code']] = rootnode

    for sbi_code_node in [node for node in section_tree if not node['IsRoot']]:
        sbi_code = sbi_code_node['Code']
        rootnode_code = sbi_code_node['Code'][:2]
        # to be depricated:
        malformed_sbi_code = sbi_code[1:] if sbi_code[0] == '0' else sbi_code
        cbsbi = CBS_sbicode(sbi_code=malformed_sbi_code,
                            title=sbi_code_node['Title'],
                            sub_cat=_get_subcat(sbi_code),
                            root_node=rootnode_set[rootnode_code])
        cbsbi.save()


def _get_subcat(sbi_code):
    try:
        return CBS_sbi_endcode.objects.filter(sbi_code=sbi_code)[0].scat
    except IndexError:
        pass

    try:
        return CBS_sbi_endcode.objects.filter(sbi_code__startswith=sbi_code)[0].scat
    except IndexError:
        if len(sbi_code) == 2:
            return CBS_sbi_subcat.objects.filter(scat='XXX')[0]
        else:
            return _get_subcat(sbi_code[:-1])


def _check_download_complete():

    if CBS_sbi_hoofdcat.objects.count() == 0:
        restore_cbs_sbi()


def restore_cbs_sbi():
    _restore_json(
        './datasets/kvkdump/fixture_files/hcat.json',
        CBS_sbi_hoofdcat, 'hcat')
    _restore_json(
        './datasets/kvkdump/fixture_files/scat.json',
        CBS_sbi_subcat, 'scat', ['hcat'])
    _restore_json(
        './datasets/kvkdump/fixture_files/sbi_endcode.json',
        CBS_sbi_endcode, 'sbi_code', ['scat'])
    _restore_json(
        './datasets/kvkdump/fixture_files/section.json',
        CBS_sbi_section, 'code')
    _restore_json(
        './datasets/kvkdump/fixture_files/rootnode.json',
        CBS_sbi_rootnode, 'code', ['section'])
    _restore_json(
        './datasets/kvkdump/fixture_files/sbi_code.json',
        CBS_sbicode, 'sbi_code', ['root_node', 'sub_cat'])


def _restore_json(filename, modelname, pkname='id', reference_fields=[]):
    with open(filename, 'r') as injson:
        indata = json.loads(injson.read())

    for rows in indata:
        newrow = modelname()
        for key, value in rows.items():
            if key == 'pk':
                setattr(newrow, pkname, value)
            elif key == 'fields':
                for fldname, fldvalue in value.items():
                    if fldname in reference_fields:
                        fldname += '_id'
                    setattr(newrow, fldname, fldvalue)
        newrow.save()


def cbsbi_table():
    _clear_cbsbi_table()
    _fill_cbsbi_table()
    _check_download_complete()
