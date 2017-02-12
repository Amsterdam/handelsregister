import random
from datetime import datetime

import factory
import json
import pytz
from django.contrib.gis.geos import Point
from factory import fuzzy

from .. import models


def restore_cbs_sbi():
    _restore_json('./datasets/kvkdump/fixture_files/hcat.json', models.CBS_sbi_hoofdcat, 'hcat')
    _restore_json('./datasets/kvkdump/fixture_files/scat.json', models.CBS_sbi_subcat, 'scat', ['hcat'])
    _restore_json('./datasets/kvkdump/fixture_files/sbi_endcode.json',  models.CBS_sbi_endcode, 'sbi_code', ['scat'])
    _restore_json('./datasets/kvkdump/fixture_files/section.json', models.CBS_sbi_section, 'code')
    _restore_json('./datasets/kvkdump/fixture_files/rootnode.json', models.CBS_sbi_rootnode, 'code', ['section'])
    _restore_json('./datasets/kvkdump/fixture_files/sbi_code.json', models.CBS_sbicode, 'sbi_code', ['root_node',
                                                                                                     'sub_cat'])


def _restore_json(filename, modelname, pkname='id', reference_fields=[]):
    with open(filename, 'r') as injson:
        indata = json.loads(injson.read())

    for rows in indata:
        newrow = modelname()
        for key, value in rows.items():
            if key == 'pk':
                setattr(newrow, pkname, value)
            elif key == 'fields':
                for fldname, fldvalue in value.items():
                    if fldname in reference_fields:
                        fldname += '_id'
                    setattr(newrow, fldname, fldvalue)
        newrow.save()


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

    @factory.post_generation
    def activiteiten(self, create, activiteiten=None, handelsnamen=None, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if handelsnamen:
            for h in handelsnamen:
                self.handelsnamen.add(h)

        if activiteiten:
            # A list of groups were passed in, use them
            for a in activiteiten:
                self.activiteiten.add(a)


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


class SBIHoofdcatFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.CBS_sbi_hoofdcat

    hcat = fuzzy.FuzzyInteger(low=100, high=109)
    hoofdcategorie = fuzzy.FuzzyText(prefix='hfdcat')


class SBISubcatFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.CBS_sbi_subcat

    scat = fuzzy.FuzzyInteger(low=1000, high=1009)
    hcat = factory.SubFactory(SBIHoofdcatFactory)
    subcategorie = fuzzy.FuzzyText(prefix='subcat')


class SBISectionFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.CBS_sbi_section

    code = 'X'
    title = fuzzy.FuzzyText(prefix='section')


class SBIRootNodeFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.CBS_sbi_rootnode

    code = '00'
    section = factory.SubFactory(SBISectionFactory)
    title = fuzzy.FuzzyText(prefix='rootnode')


class SBIcatFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.CBS_sbicode

    sbi_code = fuzzy.FuzzyInteger(low=10000, high=10009)
    title = fuzzy.FuzzyText(prefix='sbi')
    sub_cat = factory.SubFactory(SBISubcatFactory)
    root_node = factory.SubFactory(SBIRootNodeFactory)


def create_x_vestigingen(x=5):
    """
    Create some valid vestigingen with geo-location and sbi_codes

    RANDOM
    """

    vestigingen = []

    restore_cbs_sbi()  # required to allow for build of geo_vestiging
    mac = MaatschappelijkeActiviteitFactory.create()
    a1 = Activiteit.create()

    point = Point(121944.32, 487722.88)

    for i in range(x):

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
                id='{}-{}'.format(i, v),
                bezoekadres=loc_b,
                postadres=loc_p,
                activiteiten=[a1],
                maatschappelijke_activiteit=mac
            )

            vestigingen.append(ves)

    return vestigingen


def create_dataselectie_set():
    # THIS IS A RANDOM AMOUNT
    create_x_vestigingen(x=5)

    macs = models.MaatschappelijkeActiviteit.objects.all()
    personen = models.Persoon.objects.all()
    fv = models.Functievervulling.objects.all()

    for idx, m in enumerate(macs):
        if idx < len(personen) and idx % 2 == 0:
            m.eigenaar = personen[idx]
        elif idx < len(fv):
            m.eigenaar = fv[idx]
            m.save()

    sbicodes = models.CBS_sbi_endcode.objects.all()
    acnrs = models.Activiteit.objects.count() - 1
    for idx, ac in enumerate(models.Activiteit.objects.all()[:acnrs]):
        if idx < len(sbicodes):
            ac.sbi_code = sbicodes[idx].sbi_code
            ac.save()


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

    VestigingFactory.create(
        bezoekadres=loc_1,
    )

    VestigingFactory.create(
        bezoekadres=loc_2,
    )

    return [loc_1, loc_2]

#
# def build_sbi_codes():
#     hcat_rows = (
#         ("F", "BOUWNIJVERHEID"),
#         ("G", "GROOT- EN DETAILHANDEL, REPARATIE VAN AUTO’S"),
#         ("H", "VERVOER EN OPSLAG")
#     )
#
#     for hcat_id, hcat_oms in hcat_rows:
#         hcr = models.CBS_sbi_section(code=hcat_id, title=hcat_oms)
#         hcr.save()
#
#     subcat_rows = (
#         ("42", "Grond-, water- en wegenbouw (geen grondverzet)", "F"),
#         ("43", "Gespecialiseerde werkzaamheden in de bouw", "F"),
#         ("45", "Handel in en reparatie van auto's, motorfietsen en aanhangers", "G"),
#         ("46", "Groothandel en handelsbemiddeling (niet in auto's en motorfietsen)", "G"),
#         ("47", "Detailhandel (niet in auto's)", "G")
#     )
#
#     for scat, scat_oms, hcat_id in subcat_rows:
#         subcat = models.CBS_sbi_rootnode(
#             code=scat, title=scat_oms, section_id=hcat_id)
#         subcat.save()
#
#     sbicode_rows = (
#         ("421","Bouw van wegen, spoorwegen en kunstwerken","42","22274_12_22218_11"),
#         ("4211","Wegenbouw en stratenmaken","42","22274_12_22218_11"),
#         ("42111","Wegenbouw","42","22274_12_22218_11"),
#         ("42112","Stratenmaken","42","22274_12_22218_11"),
#         ("4212","Bouw van boven- en ondergrondse spoorwegen","42","22274_12_22218_11"),
#         ("432",
#         "Bouwinstallatie",
#         "43",
#         "22274_12_22219_11" ),
#         ("4321",
#         "Elektrotechnische bouwinstallatie",
#         "43",
#         "22274_12_22219_11" ),
#         ("4322",
#         "Loodgieters- en fitterswerk, installatie van sanitair en van verwarmings- en luchtbehandelingsapparatuur",
#         "43",
#         "22274_12_22219_11" ),
#         ("43221",
#         "Loodgieters- en fitterswerk, installatie van sanitair",
#         "43",
#         "22274_12_22219_11" ),
#         ("43222",
#         "Installatie van verwarmings- en luchtbehandelingsapparatuur",
#         "43",
#         "22274_12_22219_11"),
#         ("451",
#         "Handel in auto's en aanhangers, eventueel gecombineerd met reparatie",
#         "45",
#         "22272_12_22208_11" ),
#         ("4511",
#         "Handel in en reparatie van personenauto's en lichte bedrijfsauto's",
#         "45",
#         "22272_12_22208_11" ),
#         ("45111",
#         "Import van nieuwe personenauto’s en lichte bedrijfsauto's",
#         "45",
#         "22272_12_22208_11" ),
#         ("45112",
#         "Handel in en reparatie van personenauto’s en lichte bedrijfswagens (geen import van nieuwe)",
#         "45",
#         "22272_12_22208_11"),
#         ("471",
#         "Supermarkten, warenhuizen en dergelijke winkels met een algemeen assortiment",
#         "47",
#         "22272_12_22207_11" ),
#         ("4711",
#         "Supermarkten en dergelijke winkels met een algemeen assortiment voedings- en genotmiddelen",
#         "47",
#         "22272_12_22207_11" ),
#         ("4719",
#         "Warenhuizen en dergelijke winkels met een algemeen assortiment non-food",
#         "47",
#         "22272_12_22207_11" ),
#         ("47191",
#         "Warenhuizen",
#         "47",
#         "22272_12_22207_11" ),
#         ("47192",
#         "Winkels met een algemeen assortiment non-food (geen warenhuizen)",
#         "47",
#         "22272_12_22207_11")
#     )
#     for sbicode, sbi_oms, root_node_id, subcat_id in sbicode_rows:
#         c = models.CBS_sbicode(sbi_code=sbicode, title=sbi_oms, root_node_id=root_node_id)
#         c.save()
