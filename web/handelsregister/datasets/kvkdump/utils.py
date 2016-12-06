from django import db

__schema_definitions = """
CREATE TABLE kvkadrm00
(
    adrid NUMERIC(18) PRIMARY KEY NOT NULL,
    afgeschermd VARCHAR(3),
    huisletter VARCHAR,
    huisnummer NUMERIC(5),
    huisnummertoevoeging VARCHAR(5),
    identificatieaoa VARCHAR(16),
    identificatietgo VARCHAR(16),
    land VARCHAR(50),
    plaats VARCHAR(100),
    postbusnummer NUMERIC(5),
    postcode VARCHAR(6),
    postcodewoonplaats VARCHAR(220),
    regio VARCHAR(170),
    straathuisnummer VARCHAR(220),
    straatnaam VARCHAR(100),
    toevoegingadres VARCHAR(100),
    totenmetadres VARCHAR(3),
    typering VARCHAR(13),
    vesid NUMERIC(18),
    macid NUMERIC(18),
    volledigadres VARCHAR(550),
    xcoordinaat NUMERIC(9,3),
    ycoordinaat NUMERIC(9,3),
    adrhibver NUMERIC(19) DEFAULT 1 NOT NULL,
    geopunt GEOMETRY(Point,28992)
);
CREATE TABLE kvkhdnm00
(
    hdnid NUMERIC(18) PRIMARY KEY NOT NULL,
    handelsnaam VARCHAR(700),
    macid NUMERIC(18) NOT NULL,
    hdnhibver NUMERIC(19) DEFAULT 1 NOT NULL
);
CREATE TABLE kvkmacm00
(
    macid NUMERIC(18) PRIMARY KEY NOT NULL,
    beherendekamer VARCHAR(100),
    domeinnaam1 VARCHAR(300),
    domeinnaam2 VARCHAR(300),
    domeinnaam3 VARCHAR(300),
    emailadres1 VARCHAR(200),
    emailadres2 VARCHAR(200),
    emailadres3 VARCHAR(200),
    fulltimewerkzamepersonen NUMERIC(6),
    indicatieonderneming VARCHAR(3),
    kvknummer VARCHAR(8),
    naam VARCHAR(600),
    nonmailing VARCHAR(3),
    nummer1 VARCHAR(15),
    nummer2 VARCHAR(15),
    nummer3 VARCHAR(15),
    parttimewerkzamepersonen NUMERIC(6),
    prsid NUMERIC(18) NOT NULL,
    soort1 VARCHAR(10),
    soort2 VARCHAR(10),
    soort3 VARCHAR(10),
    toegangscode1 NUMERIC(4),
    toegangscode2 NUMERIC(4),
    toegangscode3 NUMERIC(4),
    totaalwerkzamepersonen NUMERIC(6),
    datumaanvang NUMERIC(8),
    datumeinde NUMERIC(8),
    laatstbijgewerkt TIMESTAMP(6) DEFAULT now() NOT NULL,
    statusobject VARCHAR(20) DEFAULT 'Bevraagd'::character varying NOT NULL,
    machibver NUMERIC(19) DEFAULT 1 NOT NULL
);
CREATE TABLE kvkprsashm00
(
    ashid NUMERIC(18) PRIMARY KEY NOT NULL,
    functie VARCHAR(20),
    prsidh NUMERIC(18),
    prsidi NUMERIC(18),
    soort VARCHAR(20),
    prsashhibver NUMERIC(19) DEFAULT 1 NOT NULL
);
CREATE TABLE kvkprsm00
(
    prsid NUMERIC(18) PRIMARY KEY NOT NULL,
    datumuitschrijving NUMERIC(8),
    datumuitspraak NUMERIC(8),
    duur VARCHAR(240),
    faillissement VARCHAR(3),
    geboortedatum NUMERIC(8),
    geboorteland VARCHAR(50),
    geboorteplaats VARCHAR(240),
    geemigreerd NUMERIC(8),
    geheim VARCHAR(3),
    geslachtsaanduiding VARCHAR(20),
    geslachtsnaam VARCHAR(240),
    handlichting VARCHAR(3),
    huwelijksdatum NUMERIC(8),
    naam VARCHAR(600),
    nummer VARCHAR(15),
    ookgenoemd VARCHAR(600),
    persoonsrechtsvorm VARCHAR(240),
    redeninsolvatie VARCHAR(50),
    rsin VARCHAR(9),
    soort VARCHAR(30),
    status VARCHAR(20),
    toegangscode NUMERIC(4),
    typering VARCHAR(40),
    uitgebreiderechtsvorm VARCHAR(240),
    verkortenaam VARCHAR(60),
    volledigenaam VARCHAR(240),
    voornamen VARCHAR(240),
    voorvoegselgeslachtsnaam VARCHAR(15),
    prshibver NUMERIC(19) DEFAULT 1 NOT NULL,
    rechtsvorm VARCHAR(50),
    doelrechtsvorm VARCHAR(50),
    rol VARCHAR(14)
);
CREATE TABLE kvkveshdnm00
(
    veshdnid NUMERIC(18) PRIMARY KEY NOT NULL,
    hdnid NUMERIC(18) NOT NULL,
    vesid NUMERIC(18) NOT NULL,
    beginrelatie NUMERIC(17),
    eindrelatie NUMERIC(17),
    veshdnhibver NUMERIC(19) DEFAULT 1 NOT NULL
);
CREATE TABLE kvkveshism00
(
    hisvesid NUMERIC(18) PRIMARY KEY NOT NULL,
    vestigingsnummer VARCHAR(12) NOT NULL,
    kvknummer VARCHAR(8) NOT NULL,
    enddate NUMERIC(17),
    hishibver NUMERIC(19) DEFAULT 1 NOT NULL
);
CREATE TABLE kvkvesm00
(
    vesid NUMERIC(18) PRIMARY KEY NOT NULL,
    datumaanvang NUMERIC(8),
    datumeinde NUMERIC(8),
    datumuitschrijving NUMERIC(8),
    domeinnaam1 VARCHAR(300),
    domeinnaam2 VARCHAR(300),
    domeinnaam3 VARCHAR(300),
    eerstehandelsnaam VARCHAR(600),
    eindgeldigheidactiviteit NUMERIC(17),
    emailadres1 VARCHAR(200),
    emailadres2 VARCHAR(200),
    emailadres3 VARCHAR(200),
    exportactiviteit VARCHAR(3),
    fulltimewerkzamepersonen NUMERIC(6),
    importactiviteit VARCHAR(3),
    indicatiehoofdvestiging VARCHAR(3) DEFAULT 'Nee'::character varying,
    macid NUMERIC(18) NOT NULL,
    naam VARCHAR(500),
    nummer1 VARCHAR(15),
    nummer2 VARCHAR(15),
    nummer3 VARCHAR(15),
    omschrijvingactiviteit VARCHAR(2000),
    ookgenoemd VARCHAR(600),
    parttimewerkzamepersonen NUMERIC(6),
    registratietijdstip NUMERIC(17),
    sbicodehoofdactiviteit NUMERIC(6),
    sbicodenevenactiviteit1 NUMERIC(6),
    sbicodenevenactiviteit2 NUMERIC(6),
    sbicodenevenactiviteit3 NUMERIC(6),
    sbiomschrijvinghoofdact VARCHAR(180),
    sbiomschrijvingnevenact1 VARCHAR(180),
    sbiomschrijvingnevenact2 VARCHAR(180),
    sbiomschrijvingnevenact3 VARCHAR(180),
    soort1 VARCHAR(10),
    soort2 VARCHAR(10),
    soort3 VARCHAR(10),
    toegangscode1 NUMERIC(4),
    toegangscode2 NUMERIC(4),
    toegangscode3 NUMERIC(4),
    totaalwerkzamepersonen NUMERIC(6),
    typeringvestiging VARCHAR(3),
    verkortenaam VARCHAR(60),
    vestigingsnummer VARCHAR(12),
    statusobject VARCHAR(20) DEFAULT 'Bevraagd'::character varying NOT NULL,
    veshibver NUMERIC(19) DEFAULT 1 NOT NULL
);
CREATE INDEX kvkadrml1 ON kvkadrm00 (typering, vesid, macid);
CREATE INDEX kvkadrml2 ON kvkadrm00 (geopunt);
ALTER TABLE kvkhdnm00 ADD FOREIGN KEY (macid) REFERENCES kvkmacm00 (macid);
CREATE UNIQUE INDEX kvkhdnml1 ON kvkhdnm00 (handelsnaam, macid);
CREATE UNIQUE INDEX kvkmacml1 ON kvkmacm00 (kvknummer);
CREATE UNIQUE INDEX kvkprsashml1 ON kvkprsashm00 (prsidh, prsidi);
CREATE INDEX kvkprsml2 ON kvkprsm00 (rsin);
CREATE UNIQUE INDEX kvkveshdnml1 ON kvkveshdnm00 (hdnid, vesid);
CREATE UNIQUE INDEX kvkveshisml1 ON kvkveshism00 (vestigingsnummer, kvknummer);
CREATE UNIQUE INDEX kvkvesml1 ON kvkvesm00 (vestigingsnummer);
"""


def generate_schema():
    with db.connection.cursor() as c:
        c.execute(__schema_definitions)
