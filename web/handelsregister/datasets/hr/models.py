from django.contrib.gis.db import models


class Persoon(models.Model):
    """
    Persoon (PRS)

    Een {Persoon} is een ieder die rechten en plichten kan hebben. {Persoon}
    wordt gebruikt als overkoepelend begrip (een verzamelnaam voor
    {NatuurlijkPersoon}, {NietNatuurlijkPersoon} en {NaamPersoon}) om er over
    te kunnen communiceren. Iedere in het handelsregister voorkomende {Persoon}
    heeft ofwel een {Eigenaarschap} en/ of minstens één {Functievervulling}
    waarmee de rol van de {Persoon} is vastgelegd.
    """

    prsid = models.CharField(primary_key=True, max_length=20)
    rechtsvorm = models.CharField(max_length=50, blank=True, null=True)
    uitgebreide_rechtsvorm = models.CharField(max_length=240, blank=True, null=True)
    volledige_naam = models.CharField(max_length=240, blank=True, null=True)


class NatuurlijkPersoon(models.Model):
    """
    Natuurlijk Persoon (NPS)

    Een {NatuurlijkPersoon} is een mens. Iedere {NatuurlijkPersoon} heeft ofwel
    een {Eigenaarschap} ofwel een {FunctieVervulling} waarbij hij optreedt in
    een relevante rol zoals bestuurder, aandeelhouder of gevolmachtigde.
    Persoonsgegevens zijn alleen authentiek indien de betreffende
    {NatuurlijkPersoon}:

    - een eigenaar is van een eenmanszaak;
    - deelneemt als maat, vennoot of lid van een rederij bij een
    {Samenwerkingsverband}.
    """

    geboortedatum = models.CharField(max_length=8, blank=True, null=True)
    geboorteplaats = models.CharField(max_length=240, blank=True, null=True)
    geboorteland = models.CharField(max_length=50, blank=True, null=True)
    naam = models.CharField(max_length=600, blank=True, null=True)
    geslachtsnaam = models.CharField(max_length=240, blank=True, null=True)
    geslachtsaanduiding = models.CharField(max_length=20, blank=True, null=True)


class NietNatuurlijkPersoon(models.Model):
    """
    Niet-natuurlijk Persoon (NNP)

    Een NietNatuurlijkPersoon is een Persoon met rechten en plichten die geen
    {NatuurlijkPersoon} is. De definitie sluit aan bij de definitie in de
    stelselcatalogus. In het handelsregister wordt de
    {EenmanszaakMetMeerdereEigenaren} en {RechtspersoonInOprichting} niet als
    {Samenwerkingsverband} geregistreerd. Voor het handelsregister worden deze
    beschouwd als niet-natuurlijke personen.
    """


class BuitenlandseVennootschap(models.Model):
    """
    Buitenlandse Vennootschap (BRV)

    Een BuitenlandseVennootschap is opgericht naar buitenlands recht.
    In het handelsregister wordt van een {BuitenlandseVennootschap}
    opgenomen: het registratienummer uit het buitenlands register,
    de naam van het register en de plaats en land waar het register
    gehouden wordt.
    """


class BinnenlandseNietNatuurlijkPersoon(models.Model):
    """
    Binnenlandse Niet-natuurlijk Persoon (BNP)

    Een {BinnenlandseNietNatuurlijkPersoon} is een {NietNatuurlijkPersoon} die
    bestaat naar Nederlands recht. Dit zijn alle Nederlandse rechtsvormen
    behalve de eenmanszaak.
    """


class FunctieVervulling(models.Model):
    """
    FunctieVervulling (FVV)

    Een {FunctieverVulling} is een vervulling door een {Persoon} van een
    functie voor een {Persoon}. Een {FunctieVervulling} geeft de relatie weer
    van de {Persoon} als functionaris en de {Persoon} als eigenaar van de
    {Onderneming} of {MaatschappelijkeActiviteit}.
    """


class Activiteit(models.Model):
    """
    Activiteit (ACT)

    Van deze entiteit zijn de entiteiten Activiteiten-CommercieleVestiging},
    {ActiviteitenNietCommerciele Vestiging en ActiviteitenRechtpersoon
    afgeleid. Zie ook de toelichting van Activiteiten bij de uitleg van het
    semantisch gegevensmodel in de officiële catalogus, paragraaf 1.5.
    """


class MaatschappelijkeActiviteit(models.Model):
    """
    Maatschappelijke Activiteit (MAC)

    Een {MaatschappelijkeActiviteit} is de activiteit van een
    {NatuurlijkPersoon} of {NietNatuurlijkPersoon}. De
    {MaatschappelijkeActiviteit} is het totaal van alle activiteiten
    uitgeoefend door een {NatuurlijkPersoon} of een {NietNatuurlijkPersoon}.
    Een {MaatschappelijkeActiviteit} kan ook als {Onderneming} voorkomen.
    """

    macid = models.CharField(primary_key=True, max_length=20)
    naam = models.CharField(max_length=600, blank=True, null=True)
    kvknummer = models.CharField(unique=True, max_length=8, blank=True, null=True)
    datum_aanvang = models.CharField(max_length=8, blank=True, null=True)
    datum_einde = models.CharField(max_length=8, blank=True, null=True)
    non_mailing = models.NullBooleanField()

    communicatiegegevens = models.ForeignKey('Communicatiegegevens', null=True, blank=True)
    vestiging = models.ForeignKey('Vestiging', blank=True, null=True)

    totaal_werkzame_personen = models.DecimalField(max_digits=8, decimal_places=0, blank=True, null=True)
    fulltime_werkzame_personen = models.DecimalField(max_digits=8, decimal_places=0, blank=True, null=True)
    parttime_werkzame_personen = models.DecimalField(max_digits=8, decimal_places=0, blank=True, null=True)


class Vestiging(models.Model):
    """
    Vestiging (VES)

    Een {Vestiging} is gebouw of een complex van gebouwen waar duurzame
    uitoefening van activiteiten van een {Onderneming} of {Rechtspersoon}
    plaatsvindt. De vestiging is een combinatie van {Activiteiten} en
    {Locatie}.
    """

    vesid = models.CharField(primary_key=True, max_length=20)

    sbicode_hoofdactiviteit = models.CharField(max_length=20, blank=True, null=True)
    sbicode_nevenactiviteit1 = models.CharField(max_length=20, blank=True, null=True)
    sbicode_nevenactiviteit2 = models.CharField(max_length=20, blank=True, null=True)
    sbicode_nevenactiviteit3 = models.CharField(max_length=20, blank=True, null=True)

    sbi_omschrijving_hoofdact = models.CharField(max_length=180, blank=True, null=True)
    sbi_omschrijving_nevenact1 = models.CharField(max_length=180, blank=True, null=True)
    sbi_omschrijving_nevenact2 = models.CharField(max_length=180, blank=True, null=True)
    sbi_omschrijving_nevenact3 = models.CharField(max_length=180, blank=True, null=True)


class Locatie(models.Model):
    """
    Locatie (LOC)

    Een {Locatie} is een aanwijsbare plek op aarde.
    """

    adrid = models.CharField(max_length=16, blank=True, null=True)
    bagid = models.CharField(max_length=16, blank=True, null=True)
    volledig_adres = models.CharField(max_length=550, blank=True, null=True)
    huisnummer_toevoeging = models.CharField(max_length=5, blank=True, null=True)
    afgeschermd = models.BooleanField()
    straat_huisnummer = models.CharField(max_length=220, blank=True, null=True)
    postcode_woonplaats = models.CharField(max_length=220, blank=True, null=True)
    regio = models.CharField(max_length=170, blank=True, null=True)
    land = models.CharField(max_length=50, blank=True, null=True)
    x_coordinaat = models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
    y_coordinaat = models.DecimalField(max_digits=9, decimal_places=3, blank=True, null=True)
    geopunt = models.PointField(srid=28992, blank=True, null=True)


class Handelsnaam(models.Model):
    """
    Handelsnaam (HN)

    Een Handelsnaam is een naam waaronder een Onderneming of een
    Vestiging van een Onderneming handelt.

    Een Onderneming mag meerdere Handelsnamen hebben. De Vestiging heeft
    tenminste één, of meerdere, Handelsna(a)m(en) waarmee die naar
    buiten treedt.

    Bij privaatrechtelijke Rechtspersonen is de statutaire naam altijd ook
    een van de Handelsnamen van de bijbehorende Onderneming.

    De Handelsnamen van de Onderneming zijn een opsomming van alle
    Handelsnamen van alle Vestigingen.

    Indien een Handelsnaam dubbel voorkomt zal deze slechts éénmaal
    worden getoond.
    """

    macid = models.CharField(primary_key=True, max_length=20)
    handelsnaam = models.CharField(max_length=500, blank=True, null=True)


class Communicatiegegevens(models.Model):
    """
    Communicatiegegevens (COM)

    In het handelsregister worden over een Rechtspersoon waaraan geen
    Onderneming toebehoord en die geen Vestiging heeft of van een
    Vestiging, opgenomen:
    - telefoonnummer
    - faxnummer
    - e-mailadres
    - internetadres
    """

    macid = models.CharField(primary_key=True, max_length=20)

    domeinnaam1 = models.CharField(max_length=300, blank=True, null=True)
    domeinnaam2 = models.CharField(max_length=300, blank=True, null=True)
    domeinnaam3 = models.CharField(max_length=300, blank=True, null=True)

    emailadres1 = models.CharField(max_length=200, blank=True, null=True)
    emailadres2 = models.CharField(max_length=200, blank=True, null=True)
    emailadres3 = models.CharField(max_length=200, blank=True, null=True)

    toegangscode1 = models.CharField(max_length=10, blank=True, null=True)
    toegangscode2 = models.CharField(max_length=10, blank=True, null=True)
    toegangscode3 = models.CharField(max_length=10, blank=True, null=True)

    communicatienummer1 = models.CharField(max_length=15, blank=True, null=True)
    communicatienummer2 = models.CharField(max_length=15, blank=True, null=True)
    communicatienummer3 = models.CharField(max_length=15, blank=True, null=True)

    soort1 = models.CharField(max_length=10, blank=True, null=True)
    soort2 = models.CharField(max_length=10, blank=True, null=True)
    soort3 = models.CharField(max_length=10, blank=True, null=True)

class RechterlijkeUitspraak(models.Model):
    """
    Abstracte klasse Rechtelijke Uitspraak (UIT)

    Een uitspraak van een rechter die invloed heeft op de
    registratie in het handelsregister. Het betreft hier een
    abstractie om andere klassen daadwerkelijk van een
    RechtelijkeUitspraak gegevens te kunnen voorzien.
    """


class Kapitaal(models.Model):
    """
    Kapitaal (KAP)

    In het handelsregister worden over een naamloze vennootschap, een besloten
    vennootschap met beperkte aansprakelijkheid, een Europese naamloze
    vennootschap of een Europese coöperatieve vennootschap opgenomen: het
    maatschappelijke kapitaal en het bedrag van het geplaatste kapitaal en van
    het gestorte deel daarvan, onderverdeeld naar soort indien er verschillende
    soorten aandelen zijn.
    """
