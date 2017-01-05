import datetime
from decimal import Decimal
from typing import List

from django.forms import model_to_dict
from django.test import TestCase

from datasets import build_hr_data
from datasets.hr import models
from datasets.kvkdump import models as kvk
from datasets.kvkdump import utils

class ImportActiviteitenTest(TestCase):
    def setUp(self):
        utils.generate_schema()

    def assertActEqual(self, expected: List[models.Activiteit], given: List[models.Activiteit]):
        expected_dicts = [model_to_dict(m, exclude='id') for m in expected]
        given_dicts = [model_to_dict(m, exclude='id') for m in given]

        self.assertListEqual(expected_dicts, given_dicts)

    def _convert(self, kvk_vestiging):
        kvk_mac = kvk.KvkMaatschappelijkeActiviteit.objects.create(
            macid=1,
            indicatieonderneming='Ja',
            kvknummer='1234567',
            naam='Willeukeurig',
            nonmailing='Ja',
            prsid=Decimal('999999999999999999'),
            datumaanvang=Decimal('19820930'),
            laatstbijgewerkt=datetime.datetime(2016, 5, 19, 9, 14, 44, 997537, tzinfo=datetime.timezone.utc),
            statusobject='Bevraagd',
            machibver=Decimal('0')
        )

        kvk_vestiging.vesid = 1
        kvk_vestiging.maatschappelijke_activiteit_id = 1
        kvk_vestiging.vestigingsnummer = '1'
        kvk_vestiging.veshibver = 0
        kvk_vestiging.plaats = 'Amsterdam'
        kvk_vestiging.volledigadres = "iets in Amsterdam"

        kvk_vestiging.save()
        build_hr_data.fill_stelselpedia()

        v = models.Vestiging.objects.get(pk=kvk_vestiging.pk)
        return list(v.activiteiten.all())

    def test_read_empty(self):
        m = kvk.KvkVestiging()

        cgs = self._convert(m)
        self.assertIsNotNone(cgs)
        self.assertListEqual([], cgs)

    def test_read_hoofdactiviteit(self):
        m = kvk.KvkVestiging(
            omschrijvingactiviteit='De exploitatie van een hotel, restaurant, bar en vergaderruimtes.',
            sbicodehoofdactiviteit=Decimal('55101'),
            sbiomschrijvinghoofdact='Hotel-restaurants',
        )

        acts = self._convert(m)
        self.assertActEqual([(models.Activiteit(
            activiteitsomschrijving='De exploitatie van een hotel, restaurant, bar en vergaderruimtes.',
            sbi_code='55101',
            sbi_omschrijving='Hotel-restaurants',
            hoofdactiviteit=True,
        ))], acts)

    def test_read_multiactiviteit(self):
        m = kvk.KvkVestiging(
            omschrijvingactiviteit='De exploitatie van een hotel, restaurant, bar en vergaderruimtes.',
            sbicodehoofdactiviteit=Decimal('55101'),
            sbicodenevenactiviteit1=Decimal('5630'),
            sbicodenevenactiviteit2=Decimal('68203'),
            sbiomschrijvinghoofdact='Hotel-restaurants',
            sbiomschrijvingnevenact1='Cafés',
            sbiomschrijvingnevenact2='Verhuur van overige woonruimte',
        )
        acts = self._convert(m)
        self.assertActEqual([models.Activiteit(
            activiteitsomschrijving='De exploitatie van een hotel, restaurant, bar en vergaderruimtes.',
            sbi_code='55101',
            sbi_omschrijving='Hotel-restaurants',
            hoofdactiviteit=True,
        ), models.Activiteit(
            sbi_code='5630',
            sbi_omschrijving='Cafés',
            hoofdactiviteit=False,
        ), models.Activiteit(
            sbi_code='68203',
            sbi_omschrijving='Verhuur van overige woonruimte',
            hoofdactiviteit=False,
        )], acts)

    def test_opschonen_activiteiten_zooi(self):
        # NOTE nog steeds nodig?
        m = kvk.KvkVestiging(
            omschrijvingactiviteit='Het schrijven van teksten, notuleren en verslaglegging',
            sbicodehoofdactiviteit=Decimal('900302'),
            sbiomschrijvinghoofdact='Scheppende kunst en documentaire schrijvers',
            sbicodenevenactiviteit1=Decimal('889922'),
            sbiomschrijvingnevenact1='Specifiek maatschappelijk werk',
            sbicodenevenactiviteit2=Decimal('620202'),
            sbiomschrijvingnevenact2='Software consultancy',
        )
        acts = self._convert(m)
        self.assertActEqual([models.Activiteit(
            activiteitsomschrijving='Het schrijven van teksten, notuleren en verslaglegging',
            sbi_code='900302',
            sbi_omschrijving='Scheppende kunst en documentaire schrijvers',
            hoofdactiviteit=True,
        ), models.Activiteit(
            sbi_code='889922',
            sbi_omschrijving='Specifiek maatschappelijk werk',
            hoofdactiviteit=False,
        ), models.Activiteit(
            sbi_code='620202',
            sbi_omschrijving='Software consultancy',
            hoofdactiviteit=False,
        )], acts)
