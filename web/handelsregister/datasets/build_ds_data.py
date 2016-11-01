
import logging
import jsonpickle
from django import db
from datasets.hr.models import DataSelectie, DataSelectieView, SbicodesPerVestiging, BetrokkenPersonen, NatuurlijkPersoon

log = logging.getLogger(__name__)

def _build_joined_ds_table():
    """
    De dataselectie wordt in 2 stappen geschreven. Eerst wordt de api data opgebouwd en in een json met een
    key per vestigings_id weggeschreven.

    Vervolgens wordt in dataselectie deze file gelezen en worden de search keys opgenomen in elastic, waardoor
    die doorzoekbaar wordt in dataselectie.
    :param cursor:
    :return:
    """

    with db.connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE hr_dataselectie")
    log.info('START opbouw dataselectie api als json')
    for vestiging_data in DataSelectieView.objects.all():
        vestiging_data.sbi_codes = SbicodesPerVestiging.objects.filter(vestiging_id=vestiging_data.vestiging_id).all()
        if len(vestiging_data.sbi_codes):
            vestiging_data.betrokkenen = BetrokkenPersonen.objects.filter(vestiging_id=vestiging_data.vestiging_id).all()
            vestiging_json = jsonpickle.encode(vestiging_data)
            ds = DataSelectie(vestiging_data.vestiging_id, vestiging_json)
            ds.save()
        else:
            log.error('Vestiging %s %s zonder sbi code' % (vestiging_data.vestiging_id, vestiging_data.naam))
    log.info('opbouw dataselectie api als json VOLTOOID')


