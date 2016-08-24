import datetime
from _decimal import Decimal

from django.test import TestCase

from datasets import build_hr_data
from datasets.kvkdump import models as kvk
from datasets.kvkdump import utils

from .. import models


class ImportVestigingTest(TestCase):
    def setUp(self):
        utils.generate_schema()

        self.kvk_mac = kvk.KvkMaatschappelijkeActiviteit.objects.create(
            macid=999999999999999999,
            indicatieonderneming='Ja',
            kvknummer='1234567',
            naam='Willeukeurig',
            nonmailing='Ja',
            prsid=999999999999999999,
            datumaanvang=19820930,
            laatstbijgewerkt=datetime.datetime(2016, 5, 19, 9, 14, 44, 997537, tzinfo=datetime.timezone.utc),
            statusobject='Bevraagd',
            machibver=0
        )

    def _convert(self, kvk_vestiging):
        build_hr_data.fill_stelselpedia()

        return models.Vestiging.objects.get(pk=kvk_vestiging.pk)

    def test_import_basic_fields(self):
        kvk_vestiging = kvk.KvkVestiging.objects.create(
            vesid=100000000000000000,
            maatschappelijke_activiteit_id=999999999999999999,
            vestigingsnummer='000033333333',
            eerstehandelsnaam='Onderneming B.V.',
            indicatiehoofdvestiging='Ja',
            typeringvestiging='CVS',
            statusobject='Bevraagd',
            veshibver=0,
            datumaanvang=20160201,
            registratietijdstip=20160322120335496,
            totaalwerkzamepersonen=0,
        )

        vestiging = self._convert(kvk_vestiging)

        self.assertIsNotNone(vestiging)
        self.assertEqual('100000000000000000', vestiging.id)
        self.assertEqual('999999999999999999', vestiging.maatschappelijke_activiteit.pk)
        self.assertEqual('000033333333', vestiging.vestigingsnummer)
        self.assertEqual('Onderneming B.V.', vestiging.naam)

        self.assertEqual(datetime.date(2016, 2, 1), vestiging.datum_aanvang)
        self.assertIsNone(vestiging.datum_einde)
        self.assertIsNone(vestiging.datum_voortzetting)
        self.assertTrue(vestiging.hoofdvestiging)

    def test_import_communicatie(self):
        kvk_vestiging = kvk.KvkVestiging.objects.create(
            vesid=100000000000000000,
            maatschappelijke_activiteit_id=999999999999999999,
            vestigingsnummer='000033333333',
            eerstehandelsnaam='Onderneming B.V.',
            typeringvestiging='CVS',
            statusobject='Bevraagd',
            veshibver=0,

            nummer1='0206666666',
            soort1='Telefoon',
            toegangscode1=31,
        )
        vestiging = self._convert(kvk_vestiging)

        comm = list(vestiging.communicatiegegevens.all())
        self.assertIsNotNone(comm)
        self.assertNotEqual([], comm)

        c = comm[0]
        self.assertIsNone(c.domeinnaam)
        self.assertIsNone(c.emailadres)
        self.assertEqual('31', c.toegangscode)
        self.assertEqual('0206666666', c.communicatie_nummer)
        self.assertEqual('Telefoon', c.soort_communicatie_nummer)

    def test_import_commercieel(self):
        kvk_vestiging = kvk.KvkVestiging.objects.create(
            vesid=100000000000000000,
            maatschappelijke_activiteit_id=999999999999999999,
            vestigingsnummer='000033333333',
            eerstehandelsnaam='Onderneming B.V.',
            typeringvestiging='CVS',
            statusobject='Bevraagd',
            veshibver=0,
            exportactiviteit='Nee',
            fulltimewerkzamepersonen=0,
            importactiviteit='Ja',
            omschrijvingactiviteit='Groothandel in bouwmaterialen algemeen assortiment',
            parttimewerkzamepersonen=0,
            registratietijdstip=20160322120335496,
            sbicodehoofdactiviteit=46739,
            sbiomschrijvinghoofdact='Groothandel in bouwmaterialen algemeen assortiment',
            totaalwerkzamepersonen=0,
        )

        vestiging = self._convert(kvk_vestiging)

        self.assertIsNotNone(vestiging.commerciele_vestiging)
        self.assertEqual(0, vestiging.commerciele_vestiging.totaal_werkzame_personen)
        self.assertEqual(0, vestiging.commerciele_vestiging.fulltime_werkzame_personen)
        self.assertEqual(0, vestiging.commerciele_vestiging.parttime_werkzame_personen)
        self.assertEqual(False, vestiging.commerciele_vestiging.export_activiteit)
        self.assertEqual(True, vestiging.commerciele_vestiging.import_activiteit)

    def test_import_niet_commercieel(self):
        kvk_vestiging = kvk.KvkVestiging.objects.create(
            vesid=222222222222222222,
            datumaanvang=20120701,
            indicatiehoofdvestiging='Ja',
            maatschappelijke_activiteit_id=999999999999999999,
            naam='Stichting',
            ookgenoemd='Superstichting',
            registratietijdstip=20120716151909809,
            typeringvestiging='NCV',
            verkortenaam='Sprst',
            vestigingsnummer='000033333333',
            statusobject='Bevraagd',
            veshibver=0
        )

        vestiging = self._convert(kvk_vestiging)

        self.assertEqual('Stichting', vestiging.naam)
        self.assertIsNotNone(vestiging.niet_commerciele_vestiging)
        self.assertEqual('Superstichting', vestiging.niet_commerciele_vestiging.ook_genoemd)
        self.assertEqual('Sprst', vestiging.niet_commerciele_vestiging.verkorte_naam)

    def test_import_adressen(self):
        kvk_vestiging = kvk.KvkVestiging.objects.create(
            vesid=100000000000000000,
            maatschappelijke_activiteit_id=999999999999999999,
            vestigingsnummer='000033333333',
            eerstehandelsnaam='Onderneming B.V.',
            typeringvestiging='CVS',
            statusobject='Bevraagd',
            veshibver=0,
            datumaanvang=20160201,
            registratietijdstip=20160322120335496,
            totaalwerkzamepersonen=0,
        )

        kvk_vestiging.adressen.add(
            kvk.KvkAdres.objects.create(
                adrid=100000000001511357,
                afgeschermd='Nee',
                huisnummer=20,
                identificatieaoa='0363200000313987',
                identificatietgo='0363010000855678',
                plaats='Amsterdam',
                postcode='1013BJ',
                straatnaam='Vlothavenweg',
                typering='bezoekLocatie',
                volledigadres='Vlothavenweg 20 1013BJ Amsterdam',
                xcoordinaat=118678.000,
                ycoordinaat=490703.000,
                adrhibver=0),
            kvk.KvkAdres.objects.create(
                adrid=100000000001511356,
                afgeschermd='Nee',
                plaats='Veghel',
                postbusnummer=229,
                postcode='5460AE',
                typering='postLocatie',
                volledigadres='Postbus 229 5460AE Veghel',
                adrhibver=0
            ))

        vestiging = self._convert(kvk_vestiging)

        self.assertIsNotNone(vestiging.postadres)
        self.assertEqual('Postbus 229 5460AE Veghel', vestiging.postadres.volledig_adres)

        self.assertIsNotNone(vestiging.bezoekadres)
        self.assertEqual('Vlothavenweg 20 1013BJ Amsterdam', vestiging.bezoekadres.volledig_adres)

    def test_import_activiteiten(self):
        kvk_vestiging = kvk.KvkVestiging.objects.create(
            vesid=100000000001511395,
            datumaanvang=19910102,
            eerstehandelsnaam='Hotel B.V.',
            maatschappelijke_activiteit_id=999999999999999999,
            omschrijvingactiviteit='De exploitatie van een hotel, restaurant, bar en vergaderruimtes.',
            sbicodehoofdactiviteit=55101,
            sbicodenevenactiviteit1=5630,
            sbicodenevenactiviteit2=68203,
            sbiomschrijvinghoofdact='Hotel-restaurants',
            sbiomschrijvingnevenact1='Cafés',
            sbiomschrijvingnevenact2='Verhuur van overige woonruimte',
            typeringvestiging='NCV',
            vestigingsnummer='1',
            statusobject='Bevraagd',
            veshibver=0
        )
        vestiging = self._convert(kvk_vestiging)

        activiteiten = list(vestiging.activiteiten.all())
        self.assertNotEqual([], activiteiten)

    def test_import_handelsnaam(self):
        kvk_vestiging = kvk.KvkVestiging.objects.create(
            vesid=100000000000000000,
            maatschappelijke_activiteit_id=999999999999999999,
            vestigingsnummer='000033333333',
            eerstehandelsnaam='Onderneming B.V.',
            typeringvestiging='CVS',
            statusobject='Bevraagd',
            veshibver=0,
        )
        kvk_handelsnaam = kvk.KvkHandelsnaam.objects.create(
            hdnid=1,
            macid_id=999999999999999999,
            handelsnaam='Handelsnaam B.V.',
            hdnhibver=0,
        )
        kvk.KvkVestigingHandelsnaam.objects.create(
            veshdnid=1,
            hdnid=kvk_handelsnaam.pk,
            vesid=kvk_vestiging.pk,
            veshdnhibver=0
        )

        vestiging = self._convert(kvk_vestiging)
        handelsnamen = list(vestiging.handelsnamen.all())
        self.assertNotEqual([], handelsnamen)

        self.assertListEqual(['Handelsnaam B.V.'], [h.handelsnaam for h in handelsnamen])
