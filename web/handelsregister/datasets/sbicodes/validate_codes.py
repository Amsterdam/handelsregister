"""
We validate the HR sbicodes with the official cbs ones
"""
import logging
import editdistance

from operator import itemgetter
from datasets.hr import models as hrmodels

from django import db


log = logging.getLogger(__name__)


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
    find sbi codes which are not defined in the
    official sbi codes
    """

    invalid = fetchrows(invalid_codes)
    log.debug('%s = invalid (fix might be possible)', len(invalid))

    return invalid


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
    codes.sub_cat
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

        print('%s - %9s - %s - "%s"' % (item[0], item[2], item[1], item[3]))

    log.debug('%s impossible to correct', len(impossible_to_correct))

    return impossible_to_correct


def fix_placable(ambiguous, zeo):
    """
    Fix sbi codes that miss a zero
    """
    pass


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
            invalid_activiteit.sbi_code=zerocode
            # save the corrected sbi code
            invalid_activiteit.save()
            # now save updated code
        else:
            # do nothing default is fine
            original_count += 1

        log.debug(f'{normalcode}, {zerocode}, {desc1[:18]}, {desc2[:18]}, {original[:18]}, {distance_desc1}, {distance_desc2}')  # noqa

    log.debug("%s - %s = Original, Suggestion", original_count, suggestion_count)


def validate():
    """
    Validate the sbi codes present in HR database
    """
    invalid = find_invalid_activiteiten()
    zero = find_0_sbicodes()
    ambiguous = find_ambiguous_sbicodes()

    not_placeable(invalid, zero)

    fix_ambiguous(ambiguous)

    fix_placable(ambiguous, zero)
