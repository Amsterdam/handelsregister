
import logging
import rapidjson
from itertools import groupby
from datetime import datetime, date
from django import db
from django.contrib.gis.geos.point import Point
from datasets.hr.models import DataSelectie, GeoVestigingen, CBS_sbi_hoofdcat, BetrokkenPersonen

log = logging.getLogger(__name__)

VESTIGING_FIELDS = ('vestigingsnummer', 'naam', 'uri', 'hoofdvestiging',
                    'locatie_type', 'geometrie')

BETROKKENEN_FIELDS = ('mac_naam', 'kvk_nummer', 'rol', 'naam', 'rechtsvorm', 'functietitel',
                      'soortbevoegdheid', 'bevoegde_naam')

def to_dict(data: object, fields: tuple) -> dict:
    result_dict = {}
    for f in fields:
        value = getattr(data, f)
        if isinstance(value, Point):
            value = [value.x, value.y]
        elif isinstance(value, datetime) or isinstance(value, date):
            value = value.isoformat()
        result_dict[f] = value
            
    return result_dict


def _build_joined_ds_table():
    """
    De dataselectie wordt in 2 stappen geschreven. Eerst wordt de api data opgebouwd en in een json met een
    key per vestiging_id weggeschreven.

    Vervolgens wordt in dataselectie deze file gelezen en worden de search keys opgenomen in elastic, waardoor
    die doorzoekbaar wordt in dataselectie.
    :param cursor:
    :return:
    """

    with db.connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE hr_dataselectie")

    # Flatten sbicodes
    log.info('Flatten sbicodes')
    sbi_values = {}
    for hoofdcat in CBS_sbi_hoofdcat.objects.select_related():
        for subcat in hoofdcat.cbs_sbi_subcat_set.all():
            for sbi in subcat.cbs_sbicodes_set.all():
                sbi_values[sbi.sbi_code] = {'sbi_code': sbi.sbi_code,
                                            'hoofdcategorie': hoofdcat.hoofdcategorie,
                                            'subcategorie': subcat.subcategorie,
                                            'sub_sub_categorie': sbi.sub_sub_categorie,
                                            'hcat': hoofdcat.hcat,
                                            'scat': subcat.scat}
    
        
    log.info('START opbouw dataselectie api als json')
    by_vestiging = groupby(GeoVestigingen.objects.order_by('vestigingsnummer'),
        lambda row: row.vestigingsnummer)
    for vestigingsnummer, vest_data in by_vestiging:
        first = True
        vestiging_dict = {}
        vestiging_dict['sbi_codes'] = vst_sbi = []
        for sbi_repeat in vest_data:
            if first:
                vestiging_dict = to_dict(sbi_repeat, VESTIGING_FIELDS)
                first = False
            log.info('vestiging gelezen')
            vst_sbi.append(sbi_values[sbi_repeat.sbi_code])
            
        log.info('sbi_codes per vestiging gelezen')
        if len(vst_sbi):
            vestiging_dict['betrokkenen'] = vst_betr = []
            for betrokken in BetrokkenPersonen.objects.\
                filter(vestiging_id=vestigingsnummer).all():
                vst_betr.append(to_dict(betrokken, BETROKKENEN_FIELDS))
            log.info('Betrokkenen gelezen')
            vestiging_json = rapidjson.dumps(vestiging_dict)
            log.info('json pickle gedaan')
            ds = DataSelectie(vestigingsnummer, vestiging_json)
            ds.save()
            log.info('geschreven')
        else:
            log.error('Vestiging %s %s zonder sbi code' % (vestigingsnummer, sbi_repeat.naam))
    log.info('opbouw dataselectie api als json VOLTOOID')


