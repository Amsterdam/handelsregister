"""
Om Handelsregister vestigingen te kunnen
selecteren en sorteren op verschillende categorien
en activiteiten maken we gebruik van de sbi codes.

SBI codes zitten in een hiërarchie(n):
  - De vraag antwoord hiërarchie
  - officiele indeling.

De vraag antwoord hiërarchie is wat makkelijker in gebruik
We willen BEIDEN soorten hiërarchien ondersteunen.

Voor actuele
gegevens is een koppeling nodig naar de SBI-hiërarchie
waarvan het CBS bronhouder is.

Ze hebben een API deze is echter niet zo makkelijk te gebruiken
dus hierbij kant en klaart json en csv output van de CBS hiërarchie
die met onderstaande code bijgewerkt kan worden
Sommige categorien hebben meer dan 100 sbi codes en deze
komen dan niet allemaal terug (groothandel, productie)

Deze code wordt onder andere gebruikte bij het
https://data.amsterdam.nl portaal.

To update json fixture files

python manage.py run_import --cbs_sbi --nocache

"""
import os
import json
import logging
import requests

from django import db

from .models import SBICodeHierarchy

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

section_url = "http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBIData/Sections"  # noqa
section_children = "http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBIData/SectionChildrenTree/" # noqa
sbi_data = "http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBIData/SbiInfo/"  # noqa

qa_url = "http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/sbianswer/getNextQuestion"  # noqa
qa_search_url = "http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBISearch/search/"  # noqa

DIRECTORY = os.path.dirname(__file__)

# module globals.
# Official SBI tree mappings
#

# code mapping
code_map = {}          # sbi code or partial  code. 'A' -> '01' -> '0102' -> ..
# node id mapping
id_map = {}            # nodes have their own id (given by the sbi.cbs api

# Question / Answers SBI tree mappings
sbi_qa_mapping = {}    # mapping of sbi codes to parent QA nodes
raw_qa_tree = {}       # QA tree 0 = root, raw json


def clean_activiteiten_key():

    """
    Clear activiteiten keys
    """

    log.debug('clear activiteiten foreign key')
    sql = """

    UPDATE hr_activiteit SET sbi_code_tree_id = null
    WHERE sbi_code_tree_id IS NOT null;
    """

    with db.connection.cursor() as cursor:
        cursor.execute(sql)


def get_fixture_path(filename):
    file_path = f'{DIRECTORY}/fixtures/{filename}'
    return file_path


def get_json_sections(
        filename='sections.json', cache=True, url=section_url):
    """
    Load the sbi.cbs categories json responses
    from file or from original url

    A, B C ...
    """

    # load from file
    if cache:
        file_path = get_fixture_path(filename)
        with open(file_path, 'r') as sectionsfile:
            cbs_sections = json.load(sectionsfile)
            return cbs_sections

    # download from API
    response = requests.get(url)
    if not response.status_code == 200:
        raise ValueError(url)
    cbs_sections = response.json()

    # save the json to file
    if not cache:
        section_path = get_fixture_path(filename)
        save_json(cbs_sections, section_path)

    return cbs_sections


def load_section_selections(all_sections, cache=True):
    """
    Each sections contains selections

    A -
       01 <-selection
       02 <-selection

    """

    # Load from file
    if cache:
        section_tree_path = get_fixture_path('section_tree.json')
        with open(section_tree_path, 'r') as sectionsfile:
            sections_tree = json.load(sectionsfile)
            return sections_tree

    # Download from API
    section_map = {}

    for section in all_sections:
        letter = section['Letter']
        section_id = section['SectionId']
        title = section['Title']

        child_section_url = f"{section_children}/{letter}"

        response = requests.get(child_section_url)

        section_map[letter] = {
            'id': section_id,
            'title': title,
            'children': response.json()
        }

    return section_map


def map_nodes_from_sections(all_sections):
    """
    Given all_section in list,
    create mappings of codes / id's to nodes

    All_sections is a dict with sections
    which contain 'children' with node list that
    have parent child relations within that list
    and sbi 'code'
    """

    for letter, section in all_sections.items():

        s_id = int(section['id'])

        # section root node
        root_node = {
            'Code': letter,
            'Id': s_id,
            'Title': section['title'],
            'ParentId': None,
        }

        id_map[s_id] = root_node
        code_map[letter] = root_node

        section_list = section['children']

        for node in section_list:
            node_id = node['Id']
            code = node['Code']
            # make sure there is consitency
            assert id_map.get(node_id) is None
            assert code_map.get(code) is None
            id_map[node_id] = node
            code_map[code] = node

    # log.debug('Codes: %s', len(code_map))
    # log.debug('ids  : %s', len(id_map))

    return code_map, id_map


def create_sbi_row(parent_list):
    """
    Given sbi parents create list of [(sbi_code, descriptions)..]
    """
    line = ""
    db_row = []

    for parent in parent_list[::-1]:
        next_code = parent['Code']
        next_title = parent['Title']
        line = f"{line}{next_code},"
        db_row.append((next_code, next_title))

    log.debug(line)

    return db_row


def create_sbi_lists():
    """
    Given mapping of codes and id's
    create hiararchy for each sbi code

    sbi_details =

    [
        [(code, title), (subcode, title), (subsub, title), (sbicode, title)],
        ..
        ..
        ..
    ]

    """

    codes = code_map.keys()
    codes = list(codes)
    codes.sort()

    sbi_details = []

    for code in codes:
        node = code_map[code]
        parent_list = [node]

        parent_id = node.get('ParentId')
        parent = id_map.get(parent_id)

        while parent:
            parent_list.append(parent)
            parent_id = parent.get('ParentId')
            parent = id_map.get(parent_id)

        db_row = create_sbi_row(parent_list)

        sbi_details.append(db_row)

    log.debug('Nodes in sbi hiararchy %s', len(sbi_details))
    return sbi_details


def create_qa_mapping():
    """
    Given sbi_qa_mapping and  qa_tree build hierarchy of sbi
    codes

    sbi_qa_details =

    {
        'sbicodeX': {
            q1: 'question 1',
            q2: 'question 2',
            q3: 'landbouw x',
        }
        ..
        ..
    }

    """
    qa_tree = {}

    for code, parent_qa in sbi_qa_mapping.items():

        pqa = parent_qa

        parent1 = pqa['parent']
        parent2 = pqa['parent']['parent']

        new_node = {
            'q3': pqa['title'],
            'q2': parent1['description'],
            'q1': parent2['description'],
        }

        qa_tree[code] = new_node
        if new_node['q1'] == 'horeca':
            print(json.dumps(pqa, indent=4))

        log.debug(
            '%15s %20s %30s',
            qa_tree[code]['q1'],
            qa_tree[code]['q2'],
            qa_tree[code]['q3'],
        )

    log.debug('sbi qa mapping: %s', len(qa_tree))

    return qa_tree


def store_sbi_details(sbi_details, qa_normalized_sbi_tree):
    """
    params: list of sbi codes and parents

    store each item in database as json
    anotated with the 'level'

    sbi_tree = {{main_category: ['01', blabla], sub_ ...}

    if there is a qa_tree available for sbicode store
    that too. sbi_deatils ~ 1400 nodes, qa-tree ~ 700 nodes
    """
    # remove old data
    SBICodeHierarchy.objects.all().delete()

    for row in sbi_details:

        levels = [
            'l1',
            'l2',
            'l3',
            'l4',
            'l5'
        ]

        sbiobject = {}

        for (code, description), level in zip(row, levels):
            sbiobject[level] = (code, description)

        row.reverse()
        code = row[0][0]   # fetch the sbicode

        # lookup qa tree if any
        x_qa_tree = qa_normalized_sbi_tree.get(code)

        new_sbi_code = SBICodeHierarchy.objects.create(
            code=code,
            title=row[0][1],
            sbi_tree=sbiobject
        )

        # add qa tree
        if x_qa_tree:
            new_sbi_code.qa_tree = x_qa_tree

        new_sbi_code.save()

    log.debug('SBI_codes in DB %s', SBICodeHierarchy.objects.count())
    log.debug(
        'SBI_codes in DB WITH QA %s',
        SBICodeHierarchy.objects.filter(qa_tree__isnull=False).count())


def save_json(data, filename):
    """
    Save the sbi code tree
    """

    with open(filename, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=True, sort_keys=True)


def load_qa_sub_sections(qa_sections, use_cache=False):
    """
    qa has a bunch of follow up questions (qa..) this is the
    second level of 3 levels. qa_sub_sections
    """
    raw_qa_tree[0] = {
        'description': 'root',
        'code': 0,
        'parent': None
    }

    qa_sub_sections = [(i['Key'], i['Value']) for i in qa_sections]

    for description, code in qa_sub_sections:

        node = {
            'description': description,
            'code': code,
            'parent': 0,
        }

        assert raw_qa_tree.get(code) is None

        raw_qa_tree[code] = node

        qa_section_description = description.split(',')[0]
        qa_section_filename = f'qa_section_{qa_section_description}.json'

        sections = get_json_sections(
            url=f'{qa_url}/{code}/1',
            filename=qa_section_filename,
            cache=use_cache)

        # load the final question layers
        load_qa_sub_sub_sections(
            node, sections['Answers'], use_cache=use_cache)


def load_qa_sub_sub_sections(parent, qa_sections, use_cache=True):
    """
    parse 3rd level questions
    """
    qa_sub_sections = [(i['Key'], i['Value']) for i in qa_sections]

    for i, (description, code) in enumerate(qa_sub_sections):

        # log.debug('%10s - %s', code, description)

        node = {
            'description': description,
            'code': code,
            'parent': parent,
        }

        raw_qa_tree[code] = node

        qa_section_description = description.split()[0].replace('/', '-')
        qa_section_filename = f'qa_section_2_{i}_{qa_section_description}.json'

        file_title = f'{i}_{qa_section_description}'

        qa_sub_sub_sections = get_json_sections(
            url=f'{qa_url}/{code}/1',
            filename=qa_section_filename,
            cache=use_cache)

        # load the final sbi codes
        sbicodes_for_subsubcategory(
            node, file_title,
            qa_sub_sub_sections['Answers'], use_cache=use_cache)


def sbicodes_for_subsubcategory(
        parent, file_title, qa_sub_sub_sections, use_cache=True):
    """
    find the sbi codes involved leave node
    """

    log.debug(qa_sub_sub_sections)

    final_section = [(i['Key'], i['Value']) for i in qa_sub_sub_sections]

    assert len(final_section) == 1

    code = final_section[0][0]

    qa_section_sbi_filename = f'qa_section_3_{file_title}.json'

    sbi_codes = get_json_sections(
        url=f'{qa_search_url}/{code}',
        filename=qa_section_sbi_filename,
        cache=use_cache)

    for sbi in sbi_codes:
        sbicode = sbi['Code']
        log.debug(sbicode)

        if sbicode in sbi_qa_mapping:
            # Code has already spot in QA tree.
            # this happens a lot with 'overige'
            log.debug('Skipped %s %s %s', sbicode, sbi['Title'], parent)
            continue

        sbi_qa_mapping[sbicode] = {
            'parent': parent,
            'title': sbi['Title'],
        }


def build_qa_sbi_code_tree(use_cache=True):
    """
    Load the QA tree from sbi.cbs.nl
    """
    section_filename = 'sections_qa.json'

    qa_sections = get_json_sections(
        url=f'{qa_url}/start/0',
        filename=section_filename,
        cache=use_cache)

    load_qa_sub_sections(
        qa_sections['Answers'], use_cache=use_cache)

    log.debug(len(raw_qa_tree))
    log.debug(len(sbi_qa_mapping))


def build_csb_sbi_code_tree(use_cache=True):
    """
    Load the official sbi tree from sbi.cbs.nl

    use_cache: do we use fixture files?
    """

    # A.. B .. C..
    sections = get_json_sections(cache=use_cache)

    # 01 , 02, 03
    section_tree = load_section_selections(sections, cache=use_cache)

    if not use_cache:
        section_tree_path = get_fixture_path('section_tree.json')
        save_json(section_tree, section_tree_path)

    map_nodes_from_sections(section_tree)

    # log.debug(json.dumps(code_map, indent=True))


def build_all_sbi_code_trees(use_cache=True):
    """
    Build both QA and Official sbi code tree
    """
    clean_activiteiten_key()
    # We use some globals.
    # if already present/filled do not bother to load them
    # again
    if id_map:
        log.debug('codes already loaded')
    else:
        build_qa_sbi_code_tree(use_cache=use_cache)
        build_csb_sbi_code_tree(use_cache=use_cache)

    normalized_qa_tree = create_qa_mapping()

    # from official tree create code lists for earch sbi
    sbi_details = create_sbi_lists()

    # after different mappings have been parsed
    # from the sbi.cbs.nl website
    # we use them to fill a table of sbi codes and their tree data
    # save result into database
    store_sbi_details(sbi_details, normalized_qa_tree)
