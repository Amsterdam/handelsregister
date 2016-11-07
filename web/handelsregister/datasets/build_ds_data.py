
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

BETROKKENEN_FIELDS = ('mac_naam', 'rol', 'naam', 'rechtsvorm', 'functietitel',
                      'soortbevoegdheid', 'bevoegde_naam')

MAATSCHAPPELIJKE_ACT_FIELDS = ('kvk_nummer', 'datum_aanvang', 'datum_einde')

LOCATIE_FIELDS = ('bag_nummeraanduiding', 'bag_adresseerbaar_object', 'straat_huisnummer',
                    'postcode_woonplaats', 'postbus_nummer', 'toevoeging_adres', 'volledig_adres')

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

    betrokken_per_vestiging = BetrokkenPersonen.objects.order_by('vestigingsnummer').iterator()
    betrokken = next(betrokken_per_vestiging)

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
                if sbi_repeat.bezoekadres and sbi_repeat.bezoekadres.bag_nummeraanduiding:
                    vestiging_dict['bezoekadres'] = to_dict(sbi_repeat.bezoekadres, LOCATIE_FIELDS)
                else:
                    vestiging_dict['bezoekadres'] = None
                if sbi_repeat.postadres and sbi_repeat.bezoekadres.bag_nummeraanduiding:
                    vestiging_dict['postadres'] = to_dict(sbi_repeat.bezoekadres, LOCATIE_FIELDS)
                else:
                    vestiging_dict['postadres'] = None

            first = False
            vst_sbi.append(sbi_values[sbi_repeat.sbi_code])
            
        if len(vst_sbi):
            vestiging_dict['betrokkenen'] = vst_betr = []
            first = True
            while betrokken.vestigingsnummer <= vestigingsnummer:
                if betrokken.vestigingsnummer == vestigingsnummer:
                    vst_betr.append(to_dict(betrokken, BETROKKENEN_FIELDS))
                    if first:
                        mac_dict = to_dict(betrokken, MAATSCHAPPELIJKE_ACT_FIELDS)
                        vestiging_dict.update(mac_dict)
                        first = False
                try:
                    betrokken = next(betrokken_per_vestiging)
                except StopIteration:
                    break
            ds = DataSelectie(vestigingsnummer, rapidjson.dumps(vestiging_dict))
            ds.save()
        else:
            log.error('Vestiging %s %s zonder sbi code' % (vestigingsnummer, sbi_repeat.naam))
    log.info('opbouw dataselectie api als json VOLTOOID')