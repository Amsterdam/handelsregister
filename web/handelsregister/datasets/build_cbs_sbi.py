"""
Slurp alle categorien en subcategorien van de cbs website af om met deze code's
de goede geo data tabel te kunnen maken.
"""

import logging
from django import db
from django.conf import settings
import requests
from datasets.hr.models import CBS_sbi_endcode, CBS_sbi_hoofdcat, CBS_sbi_subcat, \
                               CBS_sbi_section, CBS_sbi_rootnode, CBS_sbicode

log = logging.getLogger(__name__)

HARDCODED_MAPPING = {
    '30': '22214_11',
    '97': '22271_11',
    '98': '22271_11',
    '99': '22271_11'
}


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
    for sub_category_antwoord in category_data.json()['Answers']:
        scat_code = sub_category_antwoord['Value'][9:]
        scat = CBS_sbi_subcat(hcat=hcat, scat=scat_code, subcategorie=sub_category_antwoord['Key'])
        scat.save()

        category_codes = _request_exec(settings.CSB_SEARCH.format(scat_code))
        if category_codes:
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
    # create a temporary fallback for missing codes
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
    _post_process_sections()


def _process_section(section):
    section_tree_data_url = settings.CBS_SECTIONSTREE_URI.format(section.code)
    section_tree_data = _request_exec(section_tree_data_url)

    if section_tree_data:
        _process_sectiondatatree(section_tree_data, section)
        log.info("Vullen sbi codes sectie {} voltooid".format(section.code))


def _process_sectiondatatree(section_tree_data, section):
    section_tree = section_tree_data.json()

    for node in [node for node in section_tree if node['IsRoot']]:
        rootnode = CBS_sbi_rootnode(section=section, code=node['Code'], title=node['Title'])
        rootnode.save()

    for sbi_code_node in [node for node in section_tree if not node['IsRoot']]:
        sbi_code = sbi_code_node['Code']
        rootnode_code = sbi_code_node['Code'][:2]
        sub_cat = _get_subcat_direct(sbi_code)
        if sub_cat is None:
            sub_cat = CBS_sbi_subcat.objects.filter(scat='XXX')[0]

        cbsbi = CBS_sbicode(sbi_code=sbi_code,
                            title=sbi_code_node['Title'],
                            is_leaf=not sbi_code_node['HasChildren'],
                            sub_cat=sub_cat,
                            root_node_id=rootnode_code)
        cbsbi.save()


def _get_subcat_direct(sbi_code):
    try:
        return CBS_sbi_endcode.objects.filter(sbi_code=sbi_code)[0].scat
    except IndexError:
        return None


def _post_process_sections():
    _find_missing_subcats()
    _assign_missing_subcats()

    for sbi_code in CBS_sbicode.objects.filter(sub_cat_id='XXX'):
        log.info(f"ongeplaatste sbi_code: {sbi_code.sbi_code} - {sbi_code.title}")

    # to be depricated:
    _remove_starting_zeros()


def _find_missing_subcats():
    for sbi_code in CBS_sbicode.objects.filter(sub_cat_id='XXX', is_leaf=True):
        scat = _find_cbs_scat_for_missing_sbi(sbi_code.sbi_code)
        if scat is None:
            log.warning(f"No scat found for sbi_code: {sbi_code.sbi_code}")
            continue
        else:
            cbsbi = CBS_sbi_endcode(sbi_code=sbi_code.sbi_code,
                                    scat_id=scat.scat,
                                    sub_sub_categorie=sbi_code.title)
            cbsbi.save()


def _find_cbs_scat_for_missing_sbi(sbi_code):
    log.info(f"Find missing scat for {sbi_code}")
    hcat = _find_cbs_hcat_for_missing_sbi(sbi_code)

    if hcat is None:
        log.warning(f"No hcat found for sbi_code: {sbi_code}")
        return

    for subcat in CBS_sbi_subcat.objects.filter(hcat=hcat):
        search_url = settings.CSB_SEARCH.format(subcat.scat+'%20'+sbi_code)
        if _hit_for_sbicode_on(search_url, sbi_code):
            log.info(f"-- Found scat {subcat.scat} - {subcat.subcategorie} for {sbi_code}")
            return subcat
    return None


def _find_cbs_hcat_for_missing_sbi(sbi_code):
    for hcat in CBS_sbi_hoofdcat.objects.all():
        search_url = settings.CSB_SEARCH.format(hcat.hcat+'%20'+sbi_code)
        if _hit_for_sbicode_on(search_url, sbi_code):
            return hcat
    return None


def _hit_for_sbicode_on(search_url, sbi_code):
    results = _request_exec(search_url)
    if results:
        for result in results.json():
            if sbi_code == result['Code']:
                # a score > 1 means a match on more than one term
                #   we try to match on sbi_code and either hcat or scat,
                #   so a score of 1 means only 1 of the terms match,
                #   and since it's an existing sbi_code, result will always
                #   be at least 1.0
                return float(result['Score']) > 1.0
    return False


def _assign_missing_subcats():
    for sbi_code in CBS_sbicode.objects.filter(sub_cat_id='XXX'):
        new_subcat = _get_subcat(sbi_code.sbi_code)
        if not new_subcat is None:
            sbi_code.sub_cat = new_subcat
            sbi_code.save()


def  _get_subcat(sbi_code):
    possible_subcat = _get_subcat_direct(sbi_code)
    if not possible_subcat is None:
        return possible_subcat

    try:
        return CBS_sbi_endcode.objects.filter(sbi_code__startswith=sbi_code)[0].scat
    except IndexError:
        if len(sbi_code) > 2:
            return _get_subcat(sbi_code[:-1])

    if sbi_code[:2] in HARDCODED_MAPPING:
        return CBS_sbi_subcat.objects.filter(scat=HARDCODED_MAPPING[sbi_code[:2]])[0]

    return CBS_sbi_subcat.objects.filter(scat='XXX')[0]


def _remove_starting_zeros():
    # to be depricated:
    for sbi_code in CBS_sbicode.objects.filter(sbi_code__startswith='0'):
        sbi_code.sbi_code = sbi_code.sbi_code[1:]
        try:
            sbi_code.save()
        except Exception:
            pass


def cbsbi_table():
    _clear_cbsbi_table()
    _fill_cbsbi_table()
