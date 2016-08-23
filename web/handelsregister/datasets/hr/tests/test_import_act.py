from decimal import Decimal
from typing import List

from django.forms import model_to_dict
from django.test import TestCase

from datasets import build_hr_data
from datasets.hr import models
from datasets.kvkdump import models as kvk


class ImportActiviteitenTest(TestCase):
    def assertActEqual(self, expected: List[models.Activiteit], given: List[models.Activiteit]):
        expected_dicts = [model_to_dict(m, exclude='id') for m in expected]
        given_dicts = [model_to_dict(m, exclude='id') for m in given]

        self.assertListEqual(expected_dicts, given_dicts)

    def test_read_empty(self):
        m = kvk.KvkVestiging(
        )

        cgs = build_hr_data._as_activiteiten(m)
        self.assertIsNotNone(cgs)
        self.assertListEqual([], cgs)

    def test_read_hoofdactiviteit(self):
        m = kvk.KvkVestiging(
            omschrijvingactiviteit='De exploitatie van een hotel, restaurant, bar en vergaderruimtes.',
            sbicodehoofdactiviteit=Decimal('55101'),
            sbiomschrijvinghoofdact='Hotel-restaurants',
        )

        acts = build_hr_data._as_activiteiten(m)
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
        acts = build_hr_data._as_activiteiten(m)
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
        m = kvk.KvkVestiging(
            omschrijvingactiviteit='Het schrijven van teksten, notuleren en verslaglegging',
            sbicodehoofdactiviteit=Decimal('900302'),
            sbiomschrijvinghoofdact='Scheppende kunst en documentaire schrijvers',
            sbicodenevenactiviteit1=Decimal('889922'),
            sbiomschrijvingnevenact1='Specifiek maatschappelijk werk',
            sbicodenevenactiviteit2=Decimal('620202'),
            sbiomschrijvingnevenact2='Software consultancy',
        )
        acts = build_hr_data._as_activiteiten(m)
        self.assertActEqual([models.Activiteit(
            activiteitsomschrijving='Het schrijven van teksten, notuleren en verslaglegging',
            sbi_code='9003',
            sbi_omschrijving='Scheppende kunst en documentaire schrijvers',
            hoofdactiviteit=True,
        ), models.Activiteit(
            sbi_code='88992',
            sbi_omschrijving='Specifiek maatschappelijk werk',
            hoofdactiviteit=False,
        ), models.Activiteit(
            sbi_code='6202',
            sbi_omschrijving='Software consultancy',
            hoofdactiviteit=False,
        )], acts)
