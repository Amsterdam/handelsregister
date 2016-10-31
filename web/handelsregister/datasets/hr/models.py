# import uuid

from django.contrib.gis.db import models

import re


class Persoon(models.Model):
    """
    Persoon (PRS)

    Een {Persoon} is een ieder die rechten en plichten kan hebben. Persoon
    wordt gebruikt als overkoepelend begrip (een verzamelnaam voor
    NatuurlijkPersoon, NietNatuurlijkPersoon en NaamPersoon) om er over
    te kunnen communiceren. Iedere in het handelsregister voorkomende Persoon
    heeft ofwel een Eigenaarschap en/ of minstens een Functievervulling
    waarmee de rol van de Persoon is vastgelegd.

    Persoon typen:

    Natuurlijk Persoon (NPS)

    Een NatuurlijkPersoon is een mens. Iedere NatuurlijkPersoon heeft ofwel
    een {Eigenaarschap} ofwel een {Functievervulling} waarbij hij optreedt in
    een relevante rol zoals bestuurder, aandeelhouder of gevolmachtigde.
    Persoonsgegevens zijn alleen authentiek indien de betreffende
    NatuurlijkPersoon:

    - een eigenaar is van een eenmanszaak;
    - deelneemt als maat, vennoot of lid van een rederij bij een
      Samenwerkingsverband.

    Niet-natuurlijk Persoon (NNP)

    Een NietNatuurlijkPersoon is een Persoon met rechten en plichten die geen
    NatuurlijkPersoon is. De definitie sluit aan bij de definitie in de
    stelselcatalogus. In het handelsregister wordt de
    EenmanszaakMetMeerdereEigenaren en RechtspersoonInOprichting niet als
    Samenwerkingsverband geregistreerd. Voor het handelsregister worden deze
    beschouwd als niet-natuurlijke personen.

    NNP subtypen:

        - Buitenlandse Vennootschap (BRV)

            Een BuitenlandseVennootschap is opgericht naar buitenlands recht.
            In het handelsregister wordt van een {BuitenlandseVennootschap}
            opgenomen: het registratienummer uit het buitenlands register,
            de naam van het register en de plaats en land waar het register
            gehouden wordt.

        - Binnenlandse Niet-natuurlijk Persoon (BNP)

            Een BinnenlandseNietNatuurlijkPersoon is een NietNatuurlijkPersoon
            die bestaat naar Nederlands recht. Dit zijn alle Nederlandse
            rechtsvormen behalve de eenmanszaak.

    """

    type_choices = [
        ('natuurlijkPersoon', 'natuurlijkPersoon'),
        ('naamPersoon', 'naamPersoon'),
        ('buitenlandseVennootschap', 'buitenlandseVennootschap'),
        ('eenmanszaak', 'eenmanszaakMetMeerdereEigenaren'),
        ('rechtspersoon', 'rechtspersoon'),
        ('rechtspersoonInOprichting', 'rechtspersoonInOprichting'),
        ('samenwerkingsverband', 'samenwerkingsverband'),
    ]

    rol_choices = [
        ('EIGENAAR', 'EIGENAAR'),
        ('AANSPRAKELIJKE', 'AANSPRAKELIJKE'),
    ]

    id = models.DecimalField(
        primary_key=True, max_digits=18, decimal_places=0)

    rol = models.CharField(
      max_length=14, blank=True, null=True, choices=rol_choices)

    rechtsvorm = models.CharField(max_length=50, blank=True, null=True)
    uitgebreide_rechtsvorm = models.CharField(
        max_length=240, blank=True, null=True)

    volledige_naam = models.CharField(max_length=240, blank=True, null=True)

    typering = models.CharField(
        max_length=50, blank=True, null=True, choices=type_choices)

    reden_insolvatie = models.CharField(max_length=50, blank=True, null=True)

    # BeperkinginRechtshandeling (BIR)

    natuurlijkpersoon = models.OneToOneField(
        'NatuurlijkPersoon', on_delete=models.CASCADE, null=True, blank=True,
        help_text="niet null bij natuurlijkpersoon",
    )

    niet_natuurlijkpersoon = models.OneToOneField(
        'NietNatuurlijkPersoon', on_delete=models.CASCADE,
        null=True, blank=True,
        help_text="niet null bij niet-natuurlijkpersoon",
    )

    datum_aanvang = models.DateField(
        max_length=8, blank=True, null=True,
        help_text="De datum van aanvang van de MaatschappelijkeActiviteit",
    )

    datum_einde = models.DateField(
        max_length=8, blank=True, null=True,
        help_text="""
            De datum van beëindiging van de MaatschappelijkeActiviteit""",
    )

    soort = models.CharField(max_length=21, blank=True, null=True)

    datumuitschrijving = models.DateField(
        max_length=8, blank=True, null=True,
        help_text="De datum van aanvang van de MaatschappelijkeActiviteit",
    )

    naam = models.CharField(max_length=600, blank=True, null=True)

    # communicatie
    nummer = models.CharField(max_length=15, blank=True, null=True)
    toegangscode = models.DecimalField(
        max_digits=4, decimal_places=0, blank=True, null=True)

    faillissement = models.BooleanField()

    def __str__(self):
        display = "{}".format(self.id)
        if self.volledige_naam:
            display = "{} - {}".format(display, self.volledige_naam)
        if self.rechtsvorm:
            display = "{} - {}".format(display, self.rechtsvorm)
        if self.uitgebreide_rechtsvorm:
            display = "{} - {}".format(display, self.uitgebreide_rechtsvorm)

        return display


class NatuurlijkPersoon(models.Model):
    """
    Natuurlijk Persoon.
    """
    id = models.CharField(primary_key=True, max_length=20)

    voornamen = models.CharField(max_length=240, blank=True, null=True)
    geslachtsnaam = models.CharField(max_length=240, blank=True, null=True)
    geslachtsaanduiding = models.CharField(
        max_length=20, blank=True, null=True)

    huwelijksdatum = models.DateField(
            max_length=8, blank=True, null=True)

    geboortedatum = models.DateField(
            max_length=8, blank=True, null=True)

    geboorteland = models.CharField(max_length=50, blank=True, null=True)
    geboorteplaats = models.CharField(max_length=240, blank=True, null=True)


class NietNatuurlijkPersoon(models.Model):
    """
    Niet Natuurlijk Persoon.
    """
    id = models.CharField(primary_key=True, max_length=20)

    rsin = models.CharField(db_index=True, max_length=9, blank=True, null=True)
    verkorte_naam = models.CharField(max_length=60, blank=True, null=True)
    ook_genoemd = models.CharField(max_length=600, blank=True, null=True)


class Functievervulling(models.Model):
    """
    Functievervulling (FVV)

    Een FunctieverVulling is een vervulling door een Persoon van een
    functie voor een Persoon. Een Functievervulling geeft de relatie weer
    van de Persoon als functionaris en de Persoon als eigenaar van de
    Onderneming of MaatschappelijkeActiviteit.
    """

    id = models.CharField(primary_key=True, max_length=20)

    functietitel = models.CharField(max_length=20)

    heeft_aansprakelijke = models.ForeignKey(
        'Persoon', related_name='heeft_aansprakelijke', blank=True, null=True,
        help_text="",
    )

    is_aansprakelijke = models.ForeignKey(
        'Persoon', related_name='is_aansprakelijke', blank=True, null=True,
        help_text="",
    )

    soortbevoegdheid = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        naam = ''
        if self.is_aansprakelijke:
            naam = self.is_aansprakelijke.volledige_naam

        return "{} - {} - {}".format(
                naam, self.functietitel, self.soortbevoegdheid)


class Activiteit(models.Model):
    """
    Activiteit (ACT)

    Van deze entiteit zijn de entiteiten Activiteiten-CommercieleVestiging},
    {ActiviteitenNietCommerciele Vestiging en ActiviteitenRechtpersoon
    afgeleid. Zie ook de toelichting van Activiteiten bij de uitleg van het
    semantisch gegevensmodel in de officiële catalogus, paragraaf 1.5.
    """

    id = models.CharField(
        primary_key=True, max_length=21
    )

    activiteitsomschrijving = models.TextField(
        blank=True, null=True,
        help_text="""
            De omschrijving van de activiteiten die de
            Vestiging of Rechtspersoon uitoefent"""
    )
    sbi_code = models.CharField(
        max_length=5,
        help_text="De codering van de activiteit conform de SBI2008"
    )
    sbi_omschrijving = models.CharField(
        max_length=300,
        help_text="Omschrijving van de activiteit conform de SBI2008"
    )
    hoofdactiviteit = models.BooleanField(
        help_text="""
            Indicatie die aangeeft welke van de activiteiten de
            hoofdactiviteit is"""
    )


class MaatschappelijkeActiviteit(models.Model):
    """
    Maatschappelijke Activiteit (MAC)

    Een MaatschappelijkeActiviteit is de activiteit van een
    NatuurlijkPersoon of NietNatuurlijkPersoon. De
    MaatschappelijkeActiviteit is het totaal van alle activiteiten
    uitgeoefend door een NatuurlijkPersoon of een NietNatuurlijkPersoon.
    Een MaatschappelijkeActiviteit kan ook als Onderneming voorkomen.
    """
    id = models.DecimalField(
        primary_key=True, max_digits=18, decimal_places=0)

    naam = models.CharField(
        max_length=600, blank=True, null=True,
        help_text="""
            De (statutaire) naam of eerste handelsnaam van de inschrijving""",
    )
    kvk_nummer = models.CharField(
        unique=True, max_length=8, blank=True, null=True,
        help_text="""
            Betreft het identificerende gegeven
            voor de MaatschappelijkeActiviteit, het KvK-nummer""",
    )
    datum_aanvang = models.DateField(
        max_length=8, blank=True, null=True,
        help_text="De datum van aanvang van de MaatschappelijkeActiviteit",
    )
    datum_einde = models.DateField(
        max_length=8, blank=True, null=True,
        help_text="""
            De datum van beëindiging van de MaatschappelijkeActiviteit""",
    )
    incidenteel_uitlenen_arbeidskrachten = models.NullBooleanField(
        help_text="""
            Indicatie die aangeeft of de ondernemer tijdelijk arbeidskrachten
            ter beschikking stelt en dit niet onderdeel is van zijn
            'reguliere' activiteiten.""",
    )
    non_mailing = models.NullBooleanField(
        help_text="""
            Indicator die aangeeft of de inschrijving haar adresgegevens
            beschikbaar stelt voor mailing-doeleinden.""",
    )

    communicatiegegevens = models.ManyToManyField(
        'Communicatiegegevens',
        help_text="Afgeleid van communicatiegegevens van inschrijving",
    )

    activiteiten = models.ManyToManyField(
        'Activiteit',
        help_text="""
            De SBI-activiteiten van de MaatschappelijkeActiviteit is het totaal
            van alle SBI-activiteiten die voorkomen bij de
            MaatschappelijkeActiviteit behorende " NietCommercieleVestigingen
            en bij de Rechtspersoon"""
    )

    postadres = models.ForeignKey(
        'Locatie', related_name="+", blank=True, null=True,
        help_text="postadres",
    )
    bezoekadres = models.ForeignKey(
        'Locatie', related_name="+", blank=True, null=True,
        help_text="bezoekadres",
    )

    eigenaar = models.ForeignKey(
        'Persoon',
        related_name="maatschappelijke_activiteit",
        blank=True, null=True,
        help_text="",
    )

    # eigenaar zit niet ons systeem
    # iets met kvk doen?
    eigenaar_mks_id = models.DecimalField(
        blank=True, null=True,
        db_index=True, max_digits=18, decimal_places=0)

    onderneming = models.OneToOneField(
        'Onderneming', on_delete=models.CASCADE, null=True, blank=True,
        help_text="",
    )

    hoofdvestiging = models.ForeignKey(
        'Vestiging', null=True, blank=True,
    )

    def __str__(self):
        return "{}".format(self.naam)


class Onderneming(models.Model):
    """
    Van een Onderneming is sprake indien een voldoende zelfstandig optredende
    organisatorische eenheid van één of meer personen bestaat waarin door
    voldoende inbreng van arbeid of middelen, ten behoeve van derden diensten
    of goederen worden geleverd of werken tot stand worden gebracht met het
    oogmerk daarmee materieel voordeel te behalen.
    """
    id = models.CharField(primary_key=True, max_length=20)

    totaal_werkzame_personen = models.IntegerField(
        blank=True, null=True
    )

    fulltime_werkzame_personen = models.IntegerField(
        blank=True, null=True
    )

    parttime_werkzame_personen = models.IntegerField(
        blank=True, null=True
    )

    handelsnamen = models.ManyToManyField('Handelsnaam')


class CommercieleVestiging(models.Model):
    """
    Een classificatie van de Vestiging van de Onderneming.
    """
    id = models.CharField(
        primary_key=True, max_length=20
    )
    totaal_werkzame_personen = models.IntegerField(
        blank=True, null=True
    )
    fulltime_werkzame_personen = models.IntegerField(
        blank=True, null=True
    )
    parttime_werkzame_personen = models.IntegerField(
        blank=True, null=True
    )
    import_activiteit = models.NullBooleanField()
    export_activiteit = models.NullBooleanField()


class NietCommercieleVestiging(models.Model):
    id = models.CharField(
        primary_key=True, max_length=20
    )
    ook_genoemd = models.CharField(max_length=200, null=True, blank=True)
    verkorte_naam = models.CharField(max_length=60, null=True, blank=True)


class Vestiging(models.Model):
    """
    Vestiging (VES)

    Een Vestiging is gebouw of een complex van gebouwen waar duurzame
    uitoefening van activiteiten van een Onderneming of Rechtspersoon
    plaatsvindt. De vestiging is een combinatie van Activiteiten en
    Locatie.
    """

    id = models.CharField(
        primary_key=True, max_length=20
    )

    maatschappelijke_activiteit = models.ForeignKey(
        'MaatschappelijkeActiviteit',
        related_name='vestigingen',
        db_index=True,
    )

    vestigingsnummer = models.CharField(
        max_length=12, unique=True,
        help_text="Betreft het identificerende gegeven voor de Vestiging"
    )

    hoofdvestiging = models.BooleanField()

    naam = models.CharField(
        max_length=200, null=True, blank=True,
    )

    datum_aanvang = models.DateField(
        null=True, blank=True,
        help_text="De datum van aanvang van de Vestiging"
    )
    datum_einde = models.DateField(
        null=True, blank=True,
        help_text="De datum van beëindiging van de Vestiging"
    )
    datum_voortzetting = models.DateField(
        null=True, blank=True,
        help_text="De datum van voortzetting van de Vestiging"
    )
    communicatiegegevens = models.ManyToManyField(
        'Communicatiegegevens',
        help_text="Afgeleid van communicatiegegevens van inschrijving",
    )
    postadres = models.ForeignKey(
        'Locatie', related_name="+", blank=True, null=True,
        help_text="postadres",
    )
    bezoekadres = models.ForeignKey(
        'Locatie', related_name="+", blank=True, null=True,
        help_text="bezoekadres",
    )
    commerciele_vestiging = models.OneToOneField(
        'CommercieleVestiging',
        on_delete=models.CASCADE, null=True, blank=True,
    )
    niet_commerciele_vestiging = models.OneToOneField(
        'NietCommercieleVestiging',
        on_delete=models.CASCADE, null=True, blank=True,
    )

    activiteiten = models.ManyToManyField(
        'Activiteit'
    )

    handelsnamen = models.ManyToManyField(
        'Handelsnaam'
    )

    def __str__(self):

        handelsnaam = "{}".format(self.naam)
        adres = None

        if self.bezoekadres:
            adres = self.bezoekadres.volledig_adres
        elif self.postadres:
            adres = "{} (post)".format(self.postadres.volledig_adres)
        # !! NOTE this should be done in the frontend IMHO.
        if adres:
            # remove postcode
            clean_adres = re.sub("\d\d\d\d[A-Z][A-Z]", "", adres, count=1)
            return "{} - {}".format(handelsnaam, clean_adres)

        return handelsnaam


class Locatie(models.Model):
    """
    Locatie (LOC)

    Een Locatie is een aanwijsbare plek op aarde.
    """

    id = models.CharField(
        primary_key=True, max_length=18
    )
    volledig_adres = models.CharField(
        max_length=550, blank=True, null=True,
        help_text="Samengesteld adres "
    )
    toevoeging_adres = models.TextField(
        blank=True, null=True,
        help_text="Vrije tekst om een Adres nader aan te kunnen duiden"
    )
    afgeschermd = models.BooleanField(
        help_text="Geeft aan of het adres afgeschermd is of niet"
    )

    postbus_nummer = models.CharField(
        db_index=True,
        max_length=10, blank=True, null=True,
    )

    bag_numid = models.CharField(
        max_length=16, db_index=True, blank=True, null=True)

    bag_vbid = models.CharField(
        max_length=16, db_index=True, blank=True, null=True)

    bag_nummeraanduiding = models.URLField(
        max_length=200, blank=True, null=True,
        help_text="Link naar de BAG Nummeraanduiding"
    )
    bag_adresseerbaar_object = models.URLField(
        max_length=200, blank=True, null=True,
        help_text="Link naar het BAG Adresseerbaar object"
    )

    straat_huisnummer = models.CharField(max_length=220, blank=True, null=True)
    postcode_woonplaats = models.CharField(
        max_length=220, blank=True, null=True)
    regio = models.CharField(max_length=170, blank=True, null=True)
    land = models.CharField(max_length=50, blank=True, null=True)

    geometrie = models.PointField(srid=28992, blank=True, null=True)

    # Auto fix related

    # Indication if corrected by auto search
    correctie = models.NullBooleanField()
    # Last updated  (by search)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    # QS string used to fix the search data
    query_string = models.CharField(
        db_index=True,
        max_length=180, blank=True, null=True,
    )

    def __str__(self):
        return "{}".format(self.volledig_adres)


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

    id = models.CharField(
        primary_key=True, max_length=20
    )
    handelsnaam = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return "{} ({})".format(self.handelsnaam, self.onderneming.kvk_nummer)


class Communicatiegegevens(models.Model):
    """
    Communicatiegegevens (COM)

    In het handelsregister worden over een Rechtspersoon waaraan geen
    Onderneming toebehoort en die geen Vestiging heeft of van een
    Vestiging, opgenomen:
    - telefoonnummer
    - faxnummer
    - e-mailadres
    - internetadres
    """
    SOORT_COMMUNICATIE_TELEFOON = 'Telefoon'
    SOORT_COMMUNICATIE_FAX = 'Fax'
    SOORT_COMMUNICATIE_CHOICES = (
        (SOORT_COMMUNICATIE_TELEFOON, SOORT_COMMUNICATIE_TELEFOON),
        (SOORT_COMMUNICATIE_FAX, SOORT_COMMUNICATIE_FAX),
    )

    id = models.CharField(
        primary_key=True, max_length=21
    )

    domeinnaam = models.URLField(
        max_length=300, blank=True,
        null=True, help_text="Het internetadres (URL)"
    )
    emailadres = models.EmailField(
        max_length=200, blank=True, null=True,
        help_text="Het e-mailadres waar op de onderneming gemaild kan worden"
    )

    toegangscode = models.CharField(
        max_length=10, blank=True, null=True,
        help_text="""
            De internationale toegangscode van het land waarop het nummer
            (telefoon of fax) betrekking heeft"""
    )
    communicatie_nummer = models.CharField(
        max_length=15, blank=True, null=True,
        help_text="Nummer is het telefoon- of faxnummer zonder opmaak"
    )
    soort_communicatie_nummer = models.CharField(
        max_length=10, blank=True, null=True,
        choices=SOORT_COMMUNICATIE_CHOICES
    )


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


class GeoVestigingen(models.Model):
    """
    geo table of joined tables to make mapserver lighning speed
    """

    # NOTE merdere activiteiten per vestigings nummer mogelijk
    vestigingsnummer = models.CharField(
        max_length=12, db_index=True,
        help_text="Betreft het identificerende gegeven voor de Vestiging"
    )

    sbi_code_int = models.IntegerField(
        db_index=True,
        help_text="De codering van de activiteit conform de SBI2008"
    )

    sbi_code = models.CharField(
        db_index=True,
        max_length=5,
        help_text="De codering van de activiteit conform de SBI2008"
    )

    activiteitsomschrijving = models.TextField(
        blank=True, null=True,
        help_text="""
            De omschrijving van de activiteiten die de
            Vestiging of Rechtspersoon uitoefent"""
    )

    subtype = models.CharField(
        db_index=True,
        max_length=200, null=True, blank=True,
    )

    naam = models.CharField(
        max_length=200, null=True, blank=True,
    )

    uri = models.CharField(
        max_length=200, null=True, blank=True,
    )

    hoofdvestiging = models.BooleanField()

    locatie_type = models.CharField(
        max_length=1, blank=True, null=True,
        choices=[
            ('B', 'Bezoek'),
            ('P', 'Post'),
            ('V', 'Vestiging')])

    geometrie = models.PointField(srid=28992, blank=True, null=True)

    sbi_detail_group = models.CharField(
        db_index=True,
        max_length=200,
        help_text="De codering van de activiteit conform de SBI2008"
    )


class GeoVBO(models.Model):

    id = models.CharField(max_length=14, primary_key=True)

    bag_numid = models.CharField(
        max_length=16, db_index=True, blank=True, null=True)

    bag_vbid = models.CharField(
        max_length=16, db_index=True, blank=True, null=True)

    geometrie = models.PointField(srid=28992, blank=True, null=True)
