"""
We validate the HR sbicodes with the official cbs ones
"""
import logging
import os

from operator import itemgetter

import editdistance

from datasets.hr import models as hrmodels
from django import db

from .models import SBICodeHierarchy

log = logging.getLogger(__name__)

DIRECTORY = os.path.dirname(__file__)


def get_fixture_path(filename):
    file_path = f'{DIRECTORY}/fixtures/{filename}'
    return file_path


def fetchrows(sql):
    """
    Fetch rows from sql query
    """

    with db.connection.cursor() as cursor:
        cursor.execute(sql)
        results = cursor.fetchall()

        all_rows = []

        for row in results:
            all_rows.append([x for x in row])

    return all_rows


invalid_codes = """
SELECT
    vs.id,
    vs.naam,
    a.sbi_code,
    a.sbi_omschrijving
FROM
    hr_activiteit a,
    hr_vestiging_activiteiten vsa,
    hr_vestiging vs
WHERE
    vsa.vestiging_id = vs.id
    AND a.id = vsa.activiteit_id
    AND a.sbi_code NOT IN (select code from sbicodes_sbicodehierarchy)

"""


def find_invalid_activiteiten():
    """
    Find sbi codes which are not defined in the
    official sbi codes
    """

    invalid = fetchrows(invalid_codes)
    log.debug('%s = invalid (fix might be possible)', len(invalid))

    return invalid

missing_qa_tree = """
SELECT
    vs.id,
    vs.naam,
    a.sbi_code,
    a.sbi_omschrijving
FROM
    hr_activiteit a,
    hr_vestiging_activiteiten vsa,
    hr_vestiging vs
WHERE
    vsa.vestiging_id = vs.id
    AND a.id = vsa.activiteit_id
    AND a.sbi_code IN (
        select code from sbicodes_sbicodehierarchy
        where sbicodes_sbicodehierarchy.qa_tree is null
    )
"""

sbi_prefix_matches = """
SELECT
    noqa.id,
    noqa.naam,
    noqa.sbi_code,
    h.code,
    noqa.sbi_omschrijving,
    h.title
FROM (
    SELECT
        vs.id,
        vs.naam,
        a.sbi_code,
        a.sbi_omschrijving
    FROM
        hr_activiteit a,
        hr_vestiging_activiteiten vsa,
        hr_vestiging vs,
        sbicodes_sbicodehierarchy h
    WHERE
        vsa.vestiging_id = vs.id
        AND a.id = vsa.activiteit_id
        AND character_length(a.sbi_code) > 3  /* moet geen root node zijn */
        AND h.qa_tree is null                 /* match invalide leaf nodes */
        AND h.code = a.sbi_code
) as noqa, sbicodes_sbicodehierarchy h
WHERE (h.code LIKE noqa.sbi_code || '%')
  AND h.code != noqa.sbi_code
  AND h.qa_tree IS NOT null
ORDER BY sbi_code;
""" # noqa


def find_expanded_sbi_for_too_short_sbi():
    """
    Find activiteiten which do not have a qa_tree
    and thus have sbi_codes that are too short.

    the QA tree only works on fully expanded sbi codes
    but those are not always used by the HR mks source
    """
    too_short = fetchrows(sbi_prefix_matches)
    log.debug('%s = too_short', len(too_short))
    for row in too_short:
        log.debug('TOO SHORT %s %s %s', row[2], row[3], row[1])

    return too_short


def fix_too_short(too_short_rows):
    """
    For sbi codes die niet in QA boom vallen vul de missende activiteiten aan

    0 noqa.id,
    1 noqa.naam,
    2 noqa.sbi_code,
    3 h.code,
    4 noqa.sbi_omschrijving,
    5 h.title

    """

    for row in too_short_rows:

        ves = hrmodels.Vestiging.objects.get(id=row[0])

        a_count = ves.activiteiten.count()

        already_present = ves.activiteiten.filter(sbi_code=row[3])
        # log.debug(ERR)

        if list(already_present):
            continue

        log.debug('ADD %s to %s %s', row[3], row[2], row[1])

        new_activiteit = hrmodels.Activiteit.objects.create(
            #  create id
            id='%sF%s' % (row[0], a_count + 1),
            sbi_code=row[3],   # extra gevonden activiteit
            sbi_omschrijving=row[5],
            hoofdactiviteit=False
        )

        ves.activiteiten.add(new_activiteit)
        ves.save()


ambiguous_0_sql = """
SELECT
        vs.id,
        vs.naam,
        codes.hr_code,
        codes.alt_code,
        codes.title,
        codes.alt_title,
        codes.sub_cat,
        codes.alt_sub_cat,
        codes.mks_title
FROM (
SELECT
        sn.id as activiteit_id,
        sn.sbi_code as hr_code,
        s0.code  as alt_code,
        sn.title as title,
        s0.title as alt_title,
        sn.sub_cat as sub_cat,
        s0.sub_cat as alt_sub_cat,
        sn.sbi_omschrijving mks_title
FROM

    /* normale codes sn */
    (select a.id, a.sbi_code, code, title, sbi_omschrijving ,
    sbi_tree::json->'sub_category'->>0 as sub_cat
    from hr_activiteit a,  sbicodes_sbicodehierarchy h
    WHERE a.sbi_code = h.code) as sn,

    /* codes met leading 0  s0*/
    (select a.id, a.sbi_code, code, title, sbi_omschrijving ,
    sbi_tree::json->'sub_category'->>0 as sub_cat
    from hr_activiteit a,  sbicodes_sbicodehierarchy h
    WHERE '0' || a.sbi_code = h.code) as s0

    WHERE sn.sbi_code = s0.sbi_code and sn.id = s0.id
) as codes, hr_vestiging_activiteiten vsa, hr_vestiging vs

WHERE codes.activiteit_id = vsa.activiteit_id AND vsa.vestiging_id = vs.id
ORDER BY codes.hr_code, vs.naam;
"""


def find_ambiguous_sbicodes():
    """
    The 0 get's lost in some sbicodes in
    hr data now there is a range of codes
    """

    ambiguous = fetchrows(ambiguous_0_sql)
    log.debug('%s = sbicode AND 0+sbicode', len(ambiguous))
    return ambiguous


sbi_0_sql = """
SELECT
    vs.id,
    vs.naam,
    codes.sbi_code,
    codes.altcode,
    codes.title,
    codes.sub_cat,
    codes.sbi_omschrijving
FROM (

/* codes met leading 0  s0*/

SELECT
    a.id, a.sbi_code,
    code, title, sbi_omschrijving ,
    '0' || a.sbi_code as altcode,
    sbi_tree::json->'sub_category'->>0 as sub_cat
FROM hr_activiteit a,  sbicodes_sbicodehierarchy h
WHERE '0' || a.sbi_code = h.code

) as codes, hr_vestiging_activiteiten vsa, hr_vestiging vs

WHERE codes.id = vsa.activiteit_id AND vsa.vestiging_id = vs.id
ORDER BY codes.sbi_code, vs.naam;
"""


def find_0_sbicodes():
    """
    Find sbi codes that are found when we add 0
    to the original code from hr_activiteit
    """
    invalid_rows = fetchrows(sbi_0_sql)
    log.debug('%s = 0+sbicode', len(invalid_rows))

    return invalid_rows


def not_placeable(invalid_sbi, zero_sbi):
    """
    Find sbi codes that are not valid
    not even when we correct for 0
    """

    invalid_sbi = sorted(invalid_sbi, key=itemgetter(2))

    zero_set = set(i[0] for i in zero_sbi if i)

    impossible_to_correct = []

    for item in invalid_sbi:
        if item[0] in zero_set:
            continue
        impossible_to_correct.append(item)

        # print('%s - %9s - %s - "%s"' % (item[0], item[2], item[1], item[3]))

    log.debug('%s impossible to correct', len(impossible_to_correct))

    return impossible_to_correct


def fix_missing_zero(ambiguous, zero):
    """
    Fix sbi codes that miss a zero and are not ambiguous

    ~500 zero, ~200 ambiguous

    zero = [
        [
            0 vs.id,
            1 vs.naam,
            2 codes.sbi_code,
            3 codes.altcode,
            4 codes.title,
            5 codes.sub_cat
            6 codes.sbi_omschrijving
        ],
        ...
        ...
    ]

    """

    ambiguous_set = set([a[2] for a in ambiguous])

    for row in zero:
        if row[2] in ambiguous_set:
            # ambiguous cases are not solved here
            log.debug('NO 0 FIX %s', row[2])
            print(row[2])
            continue

        original_code = row[2]
        code_with_zero = row[3]
        # not ambiguous replace with existing code
        ves = hrmodels.Vestiging.objects.get(id=row[0])
        missing_zero_activiteit = ves.activiteiten.get(
            sbi_code=original_code)
        missing_zero_activiteit.sbi_code = code_with_zero
        # fix the correction
        missing_zero_activiteit.save()

        log.debug('ZERO FIX')
        log.debug(
            'ZERO FIX: %s, %s, %s, %s, %s',
            ves.naam,
            original_code, code_with_zero,
            row[6], row[4]
        )


def fix_ambiguous(ambiguous_sbi):
    """
    For each ambiguous sbi code find to most likely candidate

     0	     vs.id,
     1	     vs.naam,
     2	     codes.hr_code,
     3	     codes.alt_code,
     4	     codes.title,
     5	     codes.alt_title,
     6	     codes.sub_cat,
     7	     codes.alt_sub_cat,
     8	     codes.mks_title

    """
    original_count = 0
    suggestion_count = 0

    for row in ambiguous_sbi:

        normalcode = row[2]
        zerocode = row[3]

        desc1 = row[4]
        desc2 = row[5]
        original = row[8]

        distance_desc1 = editdistance.eval(desc1, original)
        distance_desc2 = editdistance.eval(desc2, original)

        if distance_desc1 > distance_desc2:
            # the alternative match with 0 is better
            suggestion_count += 1
            ves = hrmodels.Vestiging.objects.get(id=row[0])
            invalid_activiteit = ves.activiteiten.get(sbi_code=normalcode)
            # fix the code
            invalid_activiteit.sbi_code = zerocode
            # save the corrected sbi code
            invalid_activiteit.save()
            # now save updated code
        else:
            # do nothing default is fine
            original_count += 1

        log.debug(f'{normalcode}, {zerocode}, {desc1[:18]}, {desc2[:18]}, {original[:18]}, {distance_desc1}, {distance_desc2}')  # noqa

    log.debug("%s-%s = Original-Suggestion", original_count, suggestion_count)


sbicodes_not_in_qa_tree = """
select code, title from sbicodes_sbicodehierarchy h1
where h1.qa_tree is null
and character_length(code) > 3
and not exists (
    select h2.code from sbicodes_sbicodehierarchy h2
    where h2.qa_tree is not null
    and h2.code like h1.code || '%'
)
"""


def loadmanual_fixes():
    """
    Load manual fixes from csv

    which contains question 2 from qa_tree, sbicode and title
    """
    manual_fixes = {}

    manual_path = get_fixture_path('manual_sbicodes_201708071719.csv')
    with open(manual_path) as manualfixes:
        for line in manualfixes.readlines()[1:]:
            if not line:
                continue
            # log.debug(line)
            manual, sbicode, _ = line.split(';')
            manual = manual.replace('"', '').strip()
            sbicode = sbicode.replace('"', '').strip()

            log.debug(sbicode)
            manual_fixes[sbicode] = manual

    return manual_fixes


def find_missing_qa():
    """
    Find sbi nodes with no qa tree, which needs manual fix
    because sbc.cbs has a limit 100 on some items..
    """
    return fetchrows(sbicodes_not_in_qa_tree)


def fix_manual_missing_qa(missing_qa):
    """
    For a few sbi_codes we have a manual fixes

    we build a new qa_tree for each sbi item using the manual
    fixes this code will fix mostly sbi codes belonging to
    production
    """
    # load sql

    manual_fixes = loadmanual_fixes()

    if not missing_qa:
        log.debug("Nothing to fix")
        return

    q2_q1_map = {
        'productie': 'productie, installatie, reparatie',
        'sport': 'cultuur, sport, recreatie',
        'overige': 'overige niet hierboven genoemd',
        'groothandel': 'handel, vervoer, opslag'
    }

    for sbicode, _title in missing_qa:
        q2_solution = manual_fixes[sbicode]
        assert q2_solution

        log.debug('%s %s Resolved', sbicode, q2_solution)

        sbi_missing_qa = SBICodeHierarchy.objects.get(code=sbicode)

        q2_fix = q2_solution

        if q2_solution == 'groothandel':
            q2_fix = 'groothandel (verkoop aan andere ondernemingen, niet zelf vervaardigd)'  # noqa

        qa_tree = {
            'q1': q2_q1_map[q2_solution],
            'q2': q2_fix,
            'q3': sbi_missing_qa.title,
            'fixed': True,
        }

        sbi_missing_qa.qa_tree = qa_tree
        # fix the missing qa tree
        sbi_missing_qa.save()


def update_activiteiten():

    log.debug('update hr_activiteiten..')

    with db.connection.cursor() as cursor:
        cursor.execute("""
UPDATE hr_activiteit a
SET sbi_code_tree_id = h.code
FROM sbicodes_sbicodehierarchy h
WHERE h.code = a.sbi_code
AND sbi_code_tree_id is null
        """)


def validate():
    """
    Validate the sbi codes present in HR database
    and fix issues.
    """
    invalid = find_invalid_activiteiten()
    zero = find_0_sbicodes()
    ambiguous = find_ambiguous_sbicodes()

    fix_missing_zero(ambiguous, zero)

    log.debug(len(ambiguous))
    log.debug(len(zero))

    fix_ambiguous(ambiguous)
    not_placeable(invalid, zero)

    # some production items do not show on map.
    # fix_production(missing_qa_tree)
    # some groothandel stuff does not show on map.
    short_sbi_codes = find_expanded_sbi_for_too_short_sbi()
    fix_too_short(short_sbi_codes)

    # fix bouw / productie codes
    missing_qa = find_missing_qa()
    fix_manual_missing_qa(missing_qa)

    # fix foreign key relation
    update_activiteiten()
