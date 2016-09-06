import datetime
from decimal import Decimal

from django.test import TestCase

from datasets import build_hr_data
from datasets.kvkdump import models as kvk
from datasets.kvkdump import utils
from .. import models


class ImportPersoonTest(TestCase):
    def setUp(self):
        utils.generate_schema()

    def _convert(self, p: kvk.KvkPersoon) -> models.Persoon:
        build_hr_data.fill_stelselpedia()
        return models.Persoon.objects.get(pk=p.pk)

    def test_import_niet_natuurlijkpersoon(self):
        p = kvk.KvkPersoon.objects.create(
            prsid=Decimal('100000000000000000'),
            prshibver=Decimal('100000000000000000'),
				    datumuitschrijving=None,
				    datumuitspraak=None,
				    duur=None,
				    faillissement='Nee',
				    geboortedatum=None,
				    geboorteland=None,
				    geboorteplaats=None,
				    geemigreerd=None,
				    geheim=None,
				    geslachtsaanduiding=None,
				    geslachtsnaam=None,
				    handlichting=None,
				    huwelijksdatum=None,
				    naam='Testpersoon B.V.',
				    nummer=None,
				    ookgenoemd=None,
				    persoonsrechtsvorm='BeslotenVennootschap',
				    redeninsolvatie=None,
				    rsin='000000001',
				    soort=None,
				    status=None,
				    toegangscode=None,
				    typering='rechtspersoon',
				    uitgebreiderechtsvorm='BeslotenVennootschap',
				    verkortenaam='Testpersoon Verkort B.V.',
				    volledigenaam='Testpersoon Volledig B.V.',
				    voornamen=None,
				    voorvoegselgeslachtsnaam=None,
				    rechtsvorm=None,
				    doelrechtsvorm=None,
				    rol='EIGENAAR'
        )
        persoon = self._convert(p)

        self.assertIsNotNone(persoon)
        self.assertEqual('100000000000000000', persoon.id)
        self.assertEqual(False, persoon.faillissement)
        self.assertEqual('BeslotenVennootschap', persoon.rechtsvorm)
        self.assertEqual('000000001', persoon.niet_natuurlijkpersoon.rsin)
        self.assertEqual('rechtspersoon', persoon.typering)
        self.assertEqual('BeslotenVennootschap', persoon.uitgebreide_rechtsvorm)
        self.assertEqual('Testpersoon Verkort B.V.', persoon.niet_natuurlijkpersoon.verkorte_naam)
        self.assertEqual('Testpersoon Volledig B.V.', persoon.volledige_naam)
        self.assertEqual('EIGENAAR', persoon.rol)


    def test_import_natuurlijkpersoon(self):
        p = kvk.KvkPersoon.objects.create(
            prsid=Decimal('200000000000000000'),
            prshibver=Decimal('200000000000000000'),
				    datumuitschrijving=None,
				    datumuitspraak=None,
				    duur=None,
				    faillissement='Nee',
				    geboortedatum=None,
				    geboorteland=None,
				    geboorteplaats=None,
				    geemigreerd=None,
				    geheim=None,
				    geslachtsaanduiding=None,
				    geslachtsnaam='Testpersoon',
				    handlichting=None,
				    huwelijksdatum=None,
				    naam='Testpersoon B.V.',
				    nummer=None,
				    ookgenoemd=None,
				    persoonsrechtsvorm='Eenmanszaak',
				    redeninsolvatie=None,
				    rsin='000000001',
				    soort=None,
				    status=None,
				    toegangscode=None,
				    typering='natuurlijkPersoon',
				    uitgebreiderechtsvorm='Eenmanszaak',
				    verkortenaam=None,
				    volledigenaam='Maarten Testpersoon',
				    voornamen='Maarten',
				    voorvoegselgeslachtsnaam=None,
				    rechtsvorm=None,
				    doelrechtsvorm=None,
				    rol='EIGENAAR'
        )
        persoon = self._convert(p)

        self.assertIsNotNone(persoon)
        self.assertEqual('200000000000000000', persoon.id)
        self.assertEqual(False, persoon.faillissement)
        self.assertEqual('Eenmanszaak', persoon.rechtsvorm)
        self.assertEqual('natuurlijkPersoon', persoon.typering)
        self.assertEqual('Eenmanszaak', persoon.uitgebreide_rechtsvorm)
        self.assertEqual('Maarten Testpersoon', persoon.volledige_naam)
        self.assertEqual('EIGENAAR', persoon.rol)
