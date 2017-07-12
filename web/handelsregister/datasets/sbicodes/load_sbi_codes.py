"""

Om Handelsregister vestigingen te kunnen
selecteren en sorteren op verschillende categorien
en activiteiten maken we gebruik van de sbi codes.

SBI codes zitten in een hiërarchie. Voor actuele
gegevens is een koppeling nodig naar de SBI-hiërarchie
waarvan het CBS bronhouder is.

Ze hebben een API deze is echter niet zo makkelijk te gebruiken
dus hierbij kant en klaart json en csv output van de CBS hiërarchie
die met onderstaande code bijgewerkt kan worden

Deze code wordt onder andere gebruikte bij het
https://data.amsterdam.nl portaal.

"""
import os
import json
import logging
import requests

from .models import SBICodeHierarchy

logging.basicConfig(level=logging.DEBUG)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

section_url = "http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBIData/Sections"  # noqa
section_children = "http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBIData/SectionChildrenTree/" # noqa
sbi_data = "http://sbi.cbs.nl/cbs.typeermodule.typeerservicewebapi/api/SBIData/SbiInfo/{code}"  # noqa

REFRESH = False

DIRECTORY = os.path.dirname(__file__)


def get_fixture_path(filename):
    file_path = f'{DIRECTORY}/fixtures/{filename}'
    return file_path


def load_sections(cache=True):
    """
    Load the main cbs categories

    A, B C ...
    """

    # load from file
    if cache:
        file_path = get_fixture_path('sections.json')
        with open(file_path, 'r') as sectionsfile:
            cbs_sections = json.load(sectionsfile)
            return cbs_sections

    # download from API
    response = requests.get(section_url)
    cbs_sections = response.json()

    return cbs_sections


def load_section_selections(all_sections, cache=True):
    """
    Each sections contains selections

    A -
       01 <-selection
       02 <-selection

    """

    # load from file
    if cache:

        section_tree_path = get_fixture_path('section_tree.json')
        with open(section_tree_path, 'r') as sectionsfile:
            sections_tree = json.load(sectionsfile)
            return sections_tree

    # download from API
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
    code_map = {}
    id_map = {}

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


def load_description_for_each_code():
    """
    Leave nodes have a description for each sbi code
    which is usefull for full-text seach
    """
    pass


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


def create_sbi_table(code_map, id_map):
    """
    Given mapping of codes and id's
    create hiararchy for each sbi code
    [(code, title), ...]
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


def store_sbi_details(sbi_details):
    """
    params: list of sbi codes and parents

    store in database
    """
    # remove old data
    SBICodeHierarchy.objects.all().delete()

    for row in sbi_details:

        levels = [
            'main_category',
            'sub_category',
            'sub_sub_category',
            'sub_sub_sub_category',
            'sbicode'
        ]

        sbiobject = {}

        for (code, description), level in zip(row, levels):
            sbiobject[level] = (code, description)

        # log.debug(sbiobject)

        row.reverse()

        new_sbi_code = SBICodeHierarchy.objects.create(
            code=row[0][0],
            title=row[0][1],
            sbi_tree=sbiobject
        )

        new_sbi_code.save()

    log.debug('SBI_codes in DB %s', SBICodeHierarchy.objects.count())


def save_json(data, filename):
    """
    Save the sbi code tree
    """

    with open(filename, 'w') as jsonfile:
        json.dump(data, jsonfile, indent=True, sort_keys=True)


def build_csb_sbi_code_tree():

    # if set to false we create new json files
    use_cache = True
    # use_cache = False

    # A.. B .. C..
    sections = load_sections(cache=use_cache)

    if not use_cache:
        section_path = get_fixture_path('sections.json')
        save_json(sections, section_path)

    # 01 , 02, 03
    section_tree = load_section_selections(sections, cache=use_cache)

    if not use_cache:
        section_tree_path = get_fixture_path('section_tree.json')
        save_json(section_tree, section_tree_path)

    code_map, id_map = map_nodes_from_sections(section_tree)

    log.debug(json.dumps(code_map, indent=True))
    # 031
    # load_subsections()
    sbi_details = create_sbi_table(code_map, id_map)
    store_sbi_details(sbi_details)


if __name__ == '__main__':
    build_csb_sbi_code_tree()
