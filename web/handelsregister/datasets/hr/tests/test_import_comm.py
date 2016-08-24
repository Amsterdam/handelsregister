import datetime
from typing import List

from django.forms import model_to_dict
from django.test import TestCase

from django.utils import timezone

from datasets import build_hr_data
from datasets.hr import models
from datasets.kvkdump import models as kvk
from datasets.kvkdump import utils


class ImportCommunicatiegegevensTest(TestCase):
    def setUp(self):
        utils.generate_schema()

    def assertCommEqual(self, expected: List[models.Communicatiegegevens], cgs: List[models.Communicatiegegevens]):
        expected_dicts = [model_to_dict(m, exclude='id') for m in expected]
        given_dicts = [model_to_dict(m, exclude='id') for m in cgs]

        self.assertListEqual(expected_dicts, given_dicts)

    def _convert(self, m):
        m.macid = 1
        m.prsid = 1
        m.laatstbijgewerkt = timezone.now()
        m.statusobject = 'Bevraagd'
        m.machibver = 0
        m.save()

        build_hr_data.fill_stelselpedia()

        mac = models.MaatschappelijkeActiviteit.objects.get(pk=1)
        return list(mac.communicatiegegevens.all())

    def test_read_empty(self):
        m = kvk.KvkMaatschappelijkeActiviteit(
        )

        cgs = self._convert(m)
        self.assertIsNotNone(cgs)
        self.assertListEqual([], cgs)

    def test_read_first_set_domein(self):
        m = kvk.KvkMaatschappelijkeActiviteit(
            domeinnaam1='www.domeinnaam.nl',
            emailadres1='adres@provider.nl',
            toegangscode1='31',
            nummer1='0206987654',
            soort1='Telefoon',
        )

        cgs = self._convert(m)
        self.assertCommEqual([(models.Communicatiegegevens(
            domeinnaam='www.domeinnaam.nl',
            emailadres='adres@provider.nl',
            toegangscode='31',
            communicatie_nummer='0206987654',
            soort_communicatie_nummer='Telefoon',
        ))], cgs)

    def test_read_first_set_email(self):
        m = kvk.KvkMaatschappelijkeActiviteit(
            emailadres1='adres@provider.nl',
            toegangscode1='31',
            nummer1='0206987654',
            soort1='Telefoon',
        )

        cgs = self._convert(m)
        self.assertCommEqual([models.Communicatiegegevens(
            domeinnaam=None,
            emailadres='adres@provider.nl',
            toegangscode='31',
            communicatie_nummer='0206987654',
            soort_communicatie_nummer='Telefoon',
        )], cgs)

    def test_read_first_set_telefoon(self):
        m = kvk.KvkMaatschappelijkeActiviteit(
            toegangscode1='31',
            nummer1='0206987654',
            soort1='Telefoon',
        )

        cgs = self._convert(m)
        self.assertCommEqual([models.Communicatiegegevens(
            domeinnaam=None,
            emailadres=None,
            toegangscode='31',
            communicatie_nummer='0206987654',
            soort_communicatie_nummer='Telefoon',
        )], cgs)

    def test_read_two_sets(self):
        m = kvk.KvkMaatschappelijkeActiviteit(
            emailadres1='email@ergens.nl',
            toegangscode1=31,
            toegangscode2=31,
            nummer1='0206241111',
            nummer2='0612344321',
            soort1='Telefoon',
            soort2='Telefoon',
        )
        cgs = self._convert(m)
        self.assertCommEqual([models.Communicatiegegevens(
            emailadres='email@ergens.nl',
            toegangscode='31',
            communicatie_nummer='0206241111',
            soort_communicatie_nummer='Telefoon',
        ), models.Communicatiegegevens(
            toegangscode='31',
            communicatie_nummer='0612344321',
            soort_communicatie_nummer='Telefoon',
        )], cgs)

    def test_read_three_sets(self):
        m = kvk.KvkMaatschappelijkeActiviteit(
            emailadres1='datapunt.ois@amsterdam.nl',
            toegangscode1='31',
            toegangscode2='31',
            toegangscode3='31',
            nummer1='0610101010',
            nummer2='0207777777',
            nummer3='0208888888',
            soort1='Telefoon',
            soort2='Telefoon',
            soort3='Fax',
        )
        cgs = self._convert(m)
        self.assertCommEqual([models.Communicatiegegevens(
            emailadres='datapunt.ois@amsterdam.nl',
            toegangscode='31',
            communicatie_nummer='0610101010',
            soort_communicatie_nummer='Telefoon',
        ), models.Communicatiegegevens(
            toegangscode='31',
            communicatie_nummer='0207777777',
            soort_communicatie_nummer='Telefoon',
        ), models.Communicatiegegevens(
            toegangscode='31',
            communicatie_nummer='0208888888',
            soort_communicatie_nummer='Fax',
        )], cgs)
