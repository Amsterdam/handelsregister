from __future__ import unicode_literals

# Create your models here

from django.contrib.gis.db import models


class KvkAdres(models.Model):

    adrid = models.DecimalField(max_digits=18, decimal_places=0)

    afgeschermd = models.CharField(max_length=3, blank=True, null=True)

    huisletter = models.CharField(max_length=1, blank=True, null=True)
    huisnummer = models.DecimalField(
        max_digits=5, decimal_places=0, blank=True, null=True)
    huisnummertoevoeging = models.CharField(
        max_length=5, blank=True, null=True)

    # bag-id nummeraanduiding
    identificatieaoa = models.CharField(max_length=16, blank=True, null=True)

    # kadastrale gemeente
    identificatietgo = models.CharField(max_length=16, blank=True, null=True)

    land = models.CharField(max_length=50, blank=True, null=True)

    # plaats.
    plaats = models.CharField(max_length=100, blank=True, null=True)

    postbusnummer = models.DecimalField(
        max_digits=5, decimal_places=0, blank=True, null=True)

    postcode = models.CharField(max_length=6, blank=True, null=True)

    postcodewoonplaats = models.CharField(
        max_length=220, blank=True, null=True)
    regio = models.CharField(max_length=170, blank=True, null=True)

    straathuisnummer = models.CharField(max_length=220, blank=True, null=True)
    straatnaam = models.CharField(max_length=100, blank=True, null=True)
    toevoegingadres = models.CharField(max_length=100, blank=True, null=True)
    totenmetadres = models.CharField(max_length=3, blank=True, null=True)

    typering = models.CharField(max_length=13, blank=True, null=True)

    vesid = models.DecimalField(
        max_digits=18, decimal_places=0, blank=True, null=True)

    macid = models.DecimalField(
        max_digits=18, decimal_places=0, blank=True, null=True)

    volledigadres = models.CharField(max_length=550, blank=True, null=True)

    xcoordinaat = models.DecimalField(
        max_digits=9, decimal_places=3, blank=True, null=True)
    ycoordinaat = models.DecimalField(
        max_digits=9, decimal_places=3, blank=True, null=True)

    adrhibver = models.DecimalField(max_digits=19, decimal_places=0)

    geopunt = models.PointField(srid=28992, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'kvkadrm00'


class KvkHandelsnaam(models.Model):
    hdnid = models.DecimalField(
        primary_key=True, max_digits=18, decimal_places=0)
    handelsnaam = models.CharField(max_length=700, blank=True, null=True)

    macid = models.ForeignKey(
        'KvkMaatschappelijkeActiviteit',
        models.DO_NOTHING, db_column='macid', related_name='handelsnamen')

    hdnhibver = models.DecimalField(max_digits=19, decimal_places=0)

    class Meta:
        managed = False
        db_table = 'kvkhdnm00'
        unique_together = (('handelsnaam', 'macid'),)


class KvkMaatschappelijkeActiviteit(models.Model):
    """
    Maatschappelijk activiteit
    """
    macid = models.DecimalField(
        primary_key=True, max_digits=18, decimal_places=0)

    beherendekamer = models.CharField(max_length=100, blank=True, null=True)

    domeinnaam1 = models.CharField(max_length=300, blank=True, null=True)
    domeinnaam2 = models.CharField(max_length=300, blank=True, null=True)
    domeinnaam3 = models.CharField(max_length=300, blank=True, null=True)

    emailadres1 = models.CharField(max_length=200, blank=True, null=True)
    emailadres2 = models.CharField(max_length=200, blank=True, null=True)
    emailadres3 = models.CharField(max_length=200, blank=True, null=True)

    fulltimewerkzamepersonen = models.DecimalField(
        max_digits=6, decimal_places=0, blank=True, null=True)

    indicatieonderneming = models.CharField(
        max_length=3, blank=True, null=True)

    kvknummer = models.CharField(
        unique=True, max_length=8, blank=True, null=True)

    naam = models.CharField(max_length=600, blank=True, null=True)

    nonmailing = models.CharField(max_length=3, blank=True, null=True)

    nummer1 = models.CharField(max_length=15, blank=True, null=True)
    nummer2 = models.CharField(max_length=15, blank=True, null=True)
    nummer3 = models.CharField(max_length=15, blank=True, null=True)

    parttimewerkzamepersonen = models.DecimalField(
        max_digits=6, decimal_places=0, blank=True, null=True)

    prsid = models.DecimalField(max_digits=18, decimal_places=0)

    soort1 = models.CharField(max_length=10, blank=True, null=True)
    soort2 = models.CharField(max_length=10, blank=True, null=True)
    soort3 = models.CharField(max_length=10, blank=True, null=True)

    toegangscode1 = models.DecimalField(
        max_digits=4, decimal_places=0, blank=True, null=True)

    toegangscode2 = models.DecimalField(
        max_digits=4, decimal_places=0, blank=True, null=True)

    toegangscode3 = models.DecimalField(
        max_digits=4, decimal_places=0, blank=True, null=True)

    totaalwerkzamepersonen = models.DecimalField(
        max_digits=6, decimal_places=0, blank=True, null=True)

    datumaanvang = models.DecimalField(
        max_digits=8, decimal_places=0, blank=True, null=True)

    datumeinde = models.DecimalField(
        max_digits=8, decimal_places=0, blank=True, null=True)

    laatstbijgewerkt = models.DateTimeField()

    statusobject = models.CharField(max_length=20)

    machibver = models.DecimalField(max_digits=19, decimal_places=0)

    class Meta:
        managed = False
        db_table = 'kvkmacm00'


class KvkPrsashm00(models.Model):
    """
    Persoon
    """
    ashid = models.DecimalField(
        primary_key=True, max_digits=18, decimal_places=0)
    functie = models.CharField(max_length=20, blank=True, null=True)
    prsidh = models.DecimalField(max_digits=18, decimal_places=0)
    prsidi = models.DecimalField(max_digits=18, decimal_places=0)
    soort = models.CharField(max_length=20, blank=True, null=True)
    prsashhibver = models.DecimalField(max_digits=19, decimal_places=0)

    class Meta:
        managed = False
        db_table = 'kvkprsashm00'
        unique_together = (('prsidh', 'prsidi'),)


class KvkPersoon(models.Model):
    """
    Natuurlijk Persoon
    """
    prsid = models.DecimalField(
        primary_key=True, max_digits=18, decimal_places=0)
    datumuitschrijving = models.DecimalField(
        max_digits=8, decimal_places=0, blank=True, null=True)
    datumuitspraak = models.DecimalField(
        max_digits=8, decimal_places=0, blank=True, null=True)
    duur = models.CharField(max_length=240, blank=True, null=True)
    faillissement = models.CharField(max_length=3, blank=True, null=True)
    geboortedatum = models.DecimalField(
        max_digits=8, decimal_places=0, blank=True, null=True)
    geboorteland = models.CharField(max_length=50, blank=True, null=True)
    geboorteplaats = models.CharField(max_length=240, blank=True, null=True)
    geemigreerd = models.DecimalField(
        max_digits=8, decimal_places=0, blank=True, null=True)
    geheim = models.CharField(max_length=3, blank=True, null=True)
    geslachtsaanduiding = models.CharField(
        max_length=20, blank=True, null=True)
    geslachtsnaam = models.CharField(max_length=240, blank=True, null=True)
    handlichting = models.CharField(max_length=3, blank=True, null=True)
    huwelijksdatum = models.DecimalField(
        max_digits=8, decimal_places=0, blank=True, null=True)
    naam = models.CharField(max_length=600, blank=True, null=True)
    nummer = models.CharField(max_length=15, blank=True, null=True)
    ookgenoemd = models.CharField(max_length=600, blank=True, null=True)
    persoonsrechtsvorm = models.CharField(
        max_length=240, blank=True, null=True)
    redeninsolvatie = models.CharField(max_length=50, blank=True, null=True)
    rsin = models.CharField(max_length=9, blank=True, null=True)
    soort = models.CharField(max_length=30, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    toegangscode = models.DecimalField(
        max_digits=4, decimal_places=0, blank=True, null=True)
    typering = models.CharField(max_length=40, blank=True, null=True)
    uitgebreiderechtsvorm = models.CharField(
        max_length=240, blank=True, null=True)
    verkortenaam = models.CharField(max_length=60, blank=True, null=True)
    volledigenaam = models.CharField(max_length=240, blank=True, null=True)
    voornamen = models.CharField(max_length=240, blank=True, null=True)
    voorvoegselgeslachtsnaam = models.CharField(
        max_length=15, blank=True, null=True)
    prshibver = models.DecimalField(max_digits=19, decimal_places=0)
    rechtsvorm = models.CharField(max_length=50, blank=True, null=True)
    doelrechtsvorm = models.CharField(max_length=50, blank=True, null=True)
    rol = models.CharField(max_length=14, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'kvkprsm00'


class KvkVestigingHandelsnaam(models.Model):
    """
    Vestiging handelsnaam
    """
    veshdnid = models.DecimalField(
        primary_key=True, max_digits=18, decimal_places=0)

    hdnid = models.DecimalField(max_digits=18, decimal_places=0)
    vesid = models.DecimalField(max_digits=18, decimal_places=0)

    beginrelatie = models.DecimalField(
        max_digits=17, decimal_places=0, blank=True, null=True)
    eindrelatie = models.DecimalField(
        max_digits=17, decimal_places=0, blank=True, null=True)

    veshdnhibver = models.DecimalField(max_digits=19, decimal_places=0)

    class Meta:
        managed = False
        db_table = 'kvkveshdnm00'
        unique_together = (('hdnid', 'vesid'),)


class KvkVeshism00(models.Model):
    """
    History / gebruiken we nog niet
    """

    hisvesid = models.DecimalField(
        primary_key=True, max_digits=18, decimal_places=0)

    vestigingsnummer = models.CharField(max_length=12)

    kvknummer = models.CharField(max_length=8)

    enddate = models.DecimalField(
        max_digits=17, decimal_places=0, blank=True, null=True)

    hishibver = models.DecimalField(max_digits=19, decimal_places=0)

    class Meta:
        managed = False
        db_table = 'kvkveshism00'
        unique_together = (('vestigingsnummer', 'kvknummer'),)


class KvkVestiging(models.Model):
    """
    mks vestiging gegevens
    """

    vesid = models.DecimalField(
        primary_key=True, max_digits=18, decimal_places=0)

    datumaanvang = models.DecimalField(
        max_digits=8, decimal_places=0, blank=True, null=True)

    datumeinde = models.DecimalField(
        max_digits=8, decimal_places=0, blank=True, null=True)

    datumuitschrijving = models.DecimalField(
        max_digits=8, decimal_places=0, blank=True, null=True)

    eerstehandelsnaam = models.CharField(max_length=600, blank=True, null=True)

    eindgeldigheidactiviteit = models.DecimalField(
        max_digits=17, decimal_places=0, blank=True, null=True)

    exportactiviteit = models.CharField(max_length=3, blank=True, null=True)
    fulltimewerkzamepersonen = models.DecimalField(
        max_digits=6, decimal_places=0, blank=True, null=True)

    importactiviteit = models.CharField(max_length=3, blank=True, null=True)

    indicatiehoofdvestiging = models.CharField(
        max_length=3, blank=True, null=True)

    macid = models.DecimalField(max_digits=18, decimal_places=0)

    naam = models.CharField(max_length=500, blank=True, null=True)

    omschrijvingactiviteit = models.CharField(
        max_length=2000, blank=True, null=True)
    ookgenoemd = models.CharField(max_length=600, blank=True, null=True)

    parttimewerkzamepersonen = models.DecimalField(
        max_digits=6, decimal_places=0, blank=True, null=True)

    registratietijdstip = models.DecimalField(
        max_digits=17, decimal_places=0, blank=True, null=True)

    sbicodehoofdactiviteit = models.DecimalField(
        max_digits=6, decimal_places=0, blank=True, null=True)
    sbicodenevenactiviteit1 = models.DecimalField(
        max_digits=6, decimal_places=0, blank=True, null=True)
    sbicodenevenactiviteit2 = models.DecimalField(
        max_digits=6, decimal_places=0, blank=True, null=True)
    sbicodenevenactiviteit3 = models.DecimalField(
        max_digits=6, decimal_places=0, blank=True, null=True)

    sbiomschrijvinghoofdact = models.CharField(
        max_length=180, blank=True, null=True)
    sbiomschrijvingnevenact1 = models.CharField(
        max_length=180, blank=True, null=True)
    sbiomschrijvingnevenact2 = models.CharField(
        max_length=180, blank=True, null=True)
    sbiomschrijvingnevenact3 = models.CharField(
        max_length=180, blank=True, null=True)

    # Communicatie

    domeinnaam1 = models.CharField(max_length=300, blank=True, null=True)
    domeinnaam2 = models.CharField(max_length=300, blank=True, null=True)
    domeinnaam3 = models.CharField(max_length=300, blank=True, null=True)

    emailadres1 = models.CharField(max_length=200, blank=True, null=True)
    emailadres2 = models.CharField(max_length=200, blank=True, null=True)
    emailadres3 = models.CharField(max_length=200, blank=True, null=True)

    nummer1 = models.CharField(max_length=15, blank=True, null=True)
    nummer2 = models.CharField(max_length=15, blank=True, null=True)
    nummer3 = models.CharField(max_length=15, blank=True, null=True)

    soort1 = models.CharField(max_length=10, blank=True, null=True)
    soort2 = models.CharField(max_length=10, blank=True, null=True)
    soort3 = models.CharField(max_length=10, blank=True, null=True)

    toegangscode1 = models.DecimalField(
        max_digits=4, decimal_places=0, blank=True, null=True)
    toegangscode2 = models.DecimalField(
        max_digits=4, decimal_places=0, blank=True, null=True)
    toegangscode3 = models.DecimalField(
        max_digits=4, decimal_places=0, blank=True, null=True)

    totaalwerkzamepersonen = models.DecimalField(
        max_digits=6, decimal_places=0, blank=True, null=True)

    typeringvestiging = models.CharField(max_length=3, blank=True, null=True)

    verkortenaam = models.CharField(max_length=60, blank=True, null=True)

    vestigingsnummer = models.CharField(
        unique=True, max_length=12, blank=True, null=True)

    statusobject = models.CharField(max_length=20)

    veshibver = models.DecimalField(max_digits=19, decimal_places=0)

    class Meta:
        managed = False
        db_table = 'kvkvesm00'
