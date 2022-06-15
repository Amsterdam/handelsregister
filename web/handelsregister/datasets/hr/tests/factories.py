import random
from datetime import datetime

import faker
import factory
import pytz
from django.contrib.gis.geos import Point
from factory import fuzzy

from .. import models
from datasets.build_hr_data import fill_geo_table
from datasets.sbicodes import load_sbi_codes


class NatuurlijkePersoonFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.NatuurlijkPersoon

    id = fuzzy.FuzzyInteger(low=10000000000000, high=19000009999999)
    voornamen = fuzzy.FuzzyText('voornaam')


class PersoonFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Persoon

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=190000000000000099)
    faillissement = False
    natuurlijkpersoon = factory.SubFactory(NatuurlijkePersoonFactory)


class MaatschappelijkeActiviteitFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.MaatschappelijkeActiviteit

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=190000000000000099)
    kvk_nummer = fuzzy.FuzzyInteger(low=1, high=99999999)
    datum_aanvang = fuzzy.FuzzyDateTime(datetime(1987, 2, 4, tzinfo=pytz.utc))
    eigenaar = factory.SubFactory(PersoonFactory)


class VestigingFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Vestiging

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=190000000000000099)
    vestigingsnummer = fuzzy.FuzzyInteger(low=1, high=9999999)
    hoofdvestiging = fuzzy.FuzzyChoice(choices=[True, False])
    maatschappelijke_activiteit = factory.SubFactory(
        MaatschappelijkeActiviteitFactory)


class LocatieFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Locatie

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=190000000000000099)

    afgeschermd = fuzzy.FuzzyChoice(choices=[True, False])

    bag_numid = fuzzy.FuzzyChoice(choices=[1, 2])  # 'put_in_fixture_id'
    bag_vbid = fuzzy.FuzzyChoice(choices=[3, 4])  # 'put_in_fixture_id'
    volledig_adres = fuzzy.FuzzyText('vol_adres', length=25)
    bag_nummeraanduiding = fuzzy.FuzzyText('bag_nr_aand', length=25)
    postcode_woonplaats = fuzzy.FuzzyText(length=6)
    huisletter = fuzzy.FuzzyText(length=1)
    huisnummer = fuzzy.FuzzyInteger(1, 99999)
    huisnummertoevoeging = fuzzy.FuzzyText(length=5)
    straatnaam = fuzzy.FuzzyText('str', length=50)


class Handelsnaam(factory.DjangoModelFactory):
    class Meta:
        model = models.Handelsnaam

    id = fuzzy.FuzzyInteger(low=1000000000000, high=1900000000000)

    handelsnaam = fuzzy.FuzzyText('handelsnaam', length=25)


class Onderneming(factory.DjangoModelFactory):
    class Meta:
        model = models.Onderneming

    id = fuzzy.FuzzyInteger(low=1000000000000, high=1900000000000)
    totaal_werkzame_personen = fuzzy.FuzzyInteger(low=1, high=9000)
    fulltime_werkzame_personen = fuzzy.FuzzyInteger(low=1, high=9000)
    parttime_werkzame_personen = fuzzy.FuzzyInteger(low=1, high=9000)

    @factory.post_generation
    def handelsnamen(self, create, handelsnamen=None, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if handelsnamen:
            for h in handelsnamen:
                self.handelsnamen.add(h)


class Activiteit(factory.DjangoModelFactory):
    class Meta:
        model = models.Activiteit

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=190000000000000099)
    sbi_code = '1073'

    hoofdactiviteit = fuzzy.FuzzyChoice(choices=[True, False])


class FunctievervullingFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Functievervulling

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=190000000000000099)
    is_aansprakelijke = factory.SubFactory(PersoonFactory)
    heeft_aansprakelijke = factory.SubFactory(PersoonFactory)


def create_x_vestigingen(x=5):
    """
    Create some valid vestigingen with geo-location and sbi_codes

    RANDOM
    """

    vestigingen = []

    mac = MaatschappelijkeActiviteitFactory.create()
    a1 = Activiteit.create()

    point = Point(121944.32, 487722.88)

    for i in range(1, x+1):

        loc_b = LocatieFactory.create(
            id='{}{}'.format('b', i),
            bag_numid=i,
            bag_vbid=i,
            geometrie=point
        )

        loc_p = LocatieFactory.create(
            id=i * 100 + 1,
            bag_numid='p{}'.format(i),
            bag_vbid='p{}'.format(i),
            geometrie=point
        )

        for v in range(random.randint(1, 10)):
            ves = VestigingFactory.create(
                id='{}0{}'.format(i, v),
                bezoekadres=loc_b,
                postadres=loc_p,
                maatschappelijke_activiteit=mac
            )

            ves.activiteiten.set([a1])

            vestigingen.append(ves)

    return vestigingen


def _create_valid_actities():
    sbicodes = models.SBICodeHierarchy.objects.all()
    all_activities = list(models.Activiteit.objects.all())

    for idx, activiteit in enumerate(all_activities):
        # assign an sbi_code activitie to activiteit
        if idx < len(sbicodes):
            activiteit.sbi_code = sbicodes[idx].code
            activiteit.sbi_code_tree = sbicodes[idx]
            activiteit.save()


def create_dataselectie_set():
    """
    Create a test set for dataselectie
    """

    # required to allow for build of geo_vestiging
    load_sbi_codes.build_all_sbi_code_trees()

    create_x_vestigingen(x=5)

    macs = models.MaatschappelijkeActiviteit.objects.all()

    personen = models.Persoon.objects.all()
    fv = models.Functievervulling.objects.all()

    for idx, mac in enumerate(macs):
        if idx < len(personen) and idx % 2 == 0:
            mac.eigenaar = personen[idx]
        elif idx < len(fv):
            mac.eigenaar = fv[idx]
        mac.save()

    _create_valid_actities()

    fill_geo_table()


def create_search_test_locaties():
    """
    Create some test data for the location search completer
    """
    # locatie zonder geo maar met
    # adres en geo in fixture
    loc_1 = LocatieFactory.create(
        id='{}{}'.format('b', 1),
        bag_numid=None,
        bag_vbid=None,
        geometrie=None,
        correctie=None,
        volledig_adres='ikbestaniet 10, 1013AW, Amsterdam'
    )

    # locatie zonder geo en geen adres
    # in atlas fixture
    loc_2 = LocatieFactory.create(
        id=2 * 100 + 1,
        bag_numid=None,
        bag_vbid=None,
        geometrie=None,
        correctie=None,
        volledig_adres='ikbestawel 10 A, 1013AW, Amsterdam'

    )

    # locatie zonder geo maar met
    # adres en geo in fixture (Weesp)
    loc_3 = LocatieFactory.create(
        id=2 * 100 + 2,
        bag_numid=None,
        bag_vbid=None,
        geometrie=None,
        correctie=None,
        volledig_adres='ikbestawel 10 A, 1013AW, Weesp'

    )

    VestigingFactory.create(
        bezoekadres=loc_1,
    )

    VestigingFactory.create(
        bezoekadres=loc_2,
    )

    VestigingFactory.create(
        bezoekadres=loc_3,
    )

    return [loc_1, loc_2, loc_3]
