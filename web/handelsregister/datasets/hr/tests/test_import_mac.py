import datetime
from decimal import Decimal

from django.contrib.gis.geos import Point
from django.test import TestCase

from datasets import build_hr_data
from datasets.kvkdump import models as kvk
from datasets.kvkdump import utils
from .. import models


class ImportMaatschappelijkeActiviteitTest(TestCase):
    def setUp(self):
        utils.generate_schema()

    def _convert(self, m: kvk.KvkMaatschappelijkeActiviteit) -> models.MaatschappelijkeActiviteit:
        build_hr_data.fill_stelselpedia()
        return models.MaatschappelijkeActiviteit.objects.get(pk=m.pk)

    def test_import_typical_example(self):
        m = kvk.KvkMaatschappelijkeActiviteit.objects.create(
            macid=Decimal('100000000000000000'),
            indicatieonderneming='Ja',
            kvknummer='01010101',
            naam='Handelsregister B.V.',
            nonmailing='Ja',
            prsid=Decimal('111111111111111111'),
            datumaanvang=Decimal('19820930'),
            laatstbijgewerkt=datetime.datetime(2016, 5, 19, 9, 14, 44, 997537, tzinfo=datetime.timezone.utc),
            statusobject='Bevraagd',
            machibver=Decimal('0')
        )
        kvk.KvkHandelsnaam.objects.create(
            hdnid=Decimal('100000000001511354'),
            handelsnaam='Handelsregister B.V.',
            hdnhibver=Decimal('0'),
            macid=m
        )
        mac = self._convert(m)

        self.assertIsNotNone(mac)
        self.assertListEqual([], list(mac.communicatiegegevens.all()))
        self.assertEqual('100000000000000000', mac.id)
        self.assertEqual('01010101', mac.kvk_nummer)
        self.assertEqual('Handelsregister B.V.', mac.naam)
        self.assertEqual(datetime.date(1982, 9, 30), mac.datum_aanvang)
        self.assertIsNone(mac.datum_einde)
        self.assertEqual(True, mac.non_mailing)

        self.assertIsNotNone(mac.onderneming)
        self.assertEqual('100000000000000000', mac.onderneming.id)
        self.assertIsNone(mac.onderneming.totaal_werkzame_personen)
        self.assertIsNone(mac.onderneming.fulltime_werkzame_personen)
        self.assertIsNone(mac.onderneming.parttime_werkzame_personen)

        self.assertNotEqual([], list(mac.onderneming.handelsnamen.all()))
        self.assertEqual('Handelsregister B.V.', mac.onderneming.handelsnamen.all()[0].handelsnaam)

    def test_import_onderneming_details(self):
        m = kvk.KvkMaatschappelijkeActiviteit.objects.create(
            macid=Decimal('100000000000000000'),
            fulltimewerkzamepersonen=Decimal('3'),
            indicatieonderneming='Ja',
            kvknummer='87654321',
            naam='Bedrijf met ö',
            nonmailing='Nee',
            parttimewerkzamepersonen=Decimal('0'),
            prsid=Decimal('111111111111111111'),
            totaalwerkzamepersonen=Decimal('3'),
            datumaanvang=Decimal('19631111'),
            laatstbijgewerkt=datetime.datetime(2016, 5, 23, 15, 52, 5, 445507, tzinfo=datetime.timezone.utc),
            statusobject='Bevraagd',
            machibver=Decimal('0')
        )

        mac = self._convert(m)

        self.assertIsNotNone(mac)
        self.assertIsNotNone(mac.onderneming)
        self.assertEqual("Bedrijf met ö", mac.naam)
        self.assertEqual(3, mac.onderneming.totaal_werkzame_personen)
        self.assertEqual(3, mac.onderneming.fulltime_werkzame_personen)
        self.assertEqual(0, mac.onderneming.parttime_werkzame_personen)

    def test_import_adres_data(self):
        m = kvk.KvkMaatschappelijkeActiviteit.objects.create(
            macid=Decimal('10000000000000000'),
            kvknummer='12345678',
            naam='Stichting Handelsregister',
            nonmailing='Nee',
            prsid=Decimal('111111111111111111'),
            datumaanvang=Decimal('19980827'),
            laatstbijgewerkt=datetime.datetime(2016, 5, 20, 13, 12, 22, 248103, tzinfo=datetime.timezone.utc),
            statusobject='Bevraagd',
            machibver=Decimal('0')
        )
        m.adressen.add(kvk.KvkAdres.objects.create(
            adrid=Decimal('900000000000000000'),
            afgeschermd='Nee',
            huisnummer=Decimal('11'),
            identificatieaoa='0363200000079932',
            identificatietgo='0363010000617641',
            plaats='Amsterdam',
            postcode='1051CJ',
            straatnaam='De Kempenaerstraat',
            typering='bezoekLocatie',
            volledigadres='De Kempenaerstraat 11 1051CJ Amsterdam',
            xcoordinaat=Decimal('119767.000'),
            ycoordinaat=Decimal('488362.000'),
            adrhibver=Decimal('0'),
            geopunt=Point(119767, 488362, srid=28992))
        )
        mac = self._convert(m)

        self.assertIsNone(mac.postadres)
        self.assertIsNotNone(mac.bezoekadres)

        adr = mac.bezoekadres
        self.assertEqual('900000000000000000', adr.id)
        self.assertEqual('De Kempenaerstraat 11 1051CJ Amsterdam', adr.volledig_adres)
        self.assertIsNone(adr.toevoeging_adres)
        self.assertFalse(adr.afgeschermd)
        self.assertIsNone(adr.postbus_nummer)
        self.assertEqual('https://api.datapunt.amsterdam.nl/bag/nummeraanduiding/0363200000079932/',
                         adr.bag_nummeraanduiding)
        self.assertEqual('https://api.datapunt.amsterdam.nl/bag/verblijfsobject/0363010000617641/',
                         adr.bag_adresseerbaar_object)
        self.assertIsNone(adr.straat_huisnummer)
        self.assertIsNone(adr.postcode_woonplaats)
        self.assertIsNone(adr.regio)
        self.assertIsNone(adr.land)
        self.assertEqual(Point(119767, 488362, srid=28992), adr.geometry)

    def test_import_meerdere_adressen(self):
        m = kvk.KvkMaatschappelijkeActiviteit.objects.create(
            macid=Decimal('100000000000000000'),
            kvknummer='01122334',
            naam='Stichting Dingetjes Doen',
            nonmailing='Nee',
            prsid=Decimal('111111111111111111'),
            datumaanvang=Decimal('20071213'),
            laatstbijgewerkt=datetime.datetime(2016, 5, 20, 15, 17, 7, 371521, tzinfo=datetime.timezone.utc),
            statusobject='Bevraagd',
            machibver=Decimal(0),
        )
        m.adressen.add(kvk.KvkAdres.objects.create(
            adrid=Decimal('100000000000000000'),
            afgeschermd='Nee',
            huisnummer=Decimal('76'),
            identificatieaoa='0363200000089973',
            identificatietgo='0363010000627684',
            plaats='Amsterdam',
            postcode='1026CB',
            straatnaam='Durgerdammerdijk',
            typering='bezoekLocatie',
            volledigadres='Durgerdammerdijk 76 1026CB Amsterdam',
            xcoordinaat=Decimal('127828.000'),
            ycoordinaat=Decimal('487905.000'),
            geopunt=Point(127828, 487905),
            adrhibver=Decimal('0'),
        ), kvk.KvkAdres.objects.create(
            adrid=Decimal('200000000000000000'),
            afgeschermd='Nee',
            plaats='Amsterdam',
            postbusnummer=Decimal('36026'),
            postcode='1020MA',
            typering='postLocatie',
            volledigadres='Postbus 36026 1020MA Amsterdam',
            adrhibver=Decimal('0')
        ))

        mac = self._convert(m)

        self.assertIsNotNone(mac.postadres)
        self.assertEqual('Postbus 36026 1020MA Amsterdam', mac.postadres.volledig_adres)
        self.assertIsNone(mac.postadres.bag_nummeraanduiding)

        self.assertIsNotNone(mac.bezoekadres)
        self.assertEqual('https://api.datapunt.amsterdam.nl/bag/nummeraanduiding/0363200000089973/',
                         mac.bezoekadres.bag_nummeraanduiding)

    def test_buitenlands_adres(self):
        m = kvk.KvkMaatschappelijkeActiviteit.objects.create(
            macid=Decimal('100000000000000000'),
            kvknummer='24232221',
            naam='Stichting Administratiekantoor',
            nonmailing='Nee',
            prsid=Decimal('111111111111111111'),
            datumaanvang=Decimal('19991217'),
            laatstbijgewerkt=datetime.datetime(2016, 5, 22, 11, 13, 44, 652454, tzinfo=datetime.timezone.utc),
            statusobject='Bevraagd',
            machibver=Decimal('0')
        )
        m.adressen.add(kvk.KvkAdres.objects.create(
            adrid=Decimal('222222222222222222'),
            afgeschermd='Nee',
            land='België',
            postcodewoonplaats='1831 DIEGEM',
            straathuisnummer='Zaventemsesteenweg 162',
            typering='postLocatie',
            volledigadres='Zaventemsesteenweg 162 1831 DIEGEM België',
            adrhibver=Decimal('0')
        ))

        mac = self._convert(m)
        adr = mac.postadres

        self.assertIsNotNone(adr)
        self.assertFalse(adr.afgeschermd)
        self.assertIsNone(adr.bag_adresseerbaar_object)
        self.assertIsNone(adr.bag_nummeraanduiding)
        self.assertEqual('Zaventemsesteenweg 162', adr.straat_huisnummer)
        self.assertEqual('1831 DIEGEM', adr.postcode_woonplaats)
        self.assertIsNone(adr.regio)
        self.assertEqual('België', adr.land)
        self.assertEqual('Zaventemsesteenweg 162 1831 DIEGEM België', adr.volledig_adres)
