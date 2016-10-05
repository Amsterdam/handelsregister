# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from geo_views import migrate

from django.conf import settings


from django.contrib.sites.models import Site


def create_site(apps, *args, **kwargs):
    Site.objects.create(
        domain=settings.DATAPUNT_API_URL,
        name='API Domain'
    )


def delete_site(apps, *args, **kwargs):
    Site.objects.filter(name='API Domain').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('sites', '__first__'),
        ('hr', '__first__'),
    ]

    operations = [
        # set the site name
        migrations.RunPython(code=create_site, reverse_code=delete_site),
        # create the hr views
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties",
            sql="""SELECT * FROM hr_geovestigingen"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_bouw",
            sql="""
SELECT * FROM hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group in (
        'bouw/utiliteitsbouw algemeen / klusbedrijf',
        'bouw overig',
        'bouwinstallatie',
        'afwerking van gebouwen',
        'dak- en overige gespecialiseerde bouw',
        'grond, water, wegenbouw',
        'bouw/utiliteitsbouw algemeen / klusbedrijf')
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_overheid_onderwijs_zorg",
            sql="""
SELECT * FROM hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group in (
        'onderwijs',
        'gezondheids- en welzijnszorg',
        'overheid')
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_productie_installatie_reparatie",
            sql="""
SELECT * FROM hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group in (
        'arbeidsbemiddeling, uitzendbureaus, uitleenbureaus',
        'overige zakelijke dienstverlening',
        'reclame en marktonderzoek',
        'interieurarchitecten',
        'managementadvies, economisch advies',
        'technisch ontwerp, advies, keuring/research',
        'design',
        'public relationsbureaus',
        'advocaten rechtskundige diensten, notarissen',
        'architecten',
        'accountancy, administratie')
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_handel_vervoer_opslag",
            sql="""
SELECT * FROM hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group in (
        'vervoer',
        'detailhandel (verkoop aan consumenten, niet zelf vervaardigd)',
        'handelsbemiddeling (tussenpersoon, verkoopt niet zelf)',
        'opslag',
        'dienstverlening vervoer',
        'handel en reparatie van auto s',
        'groothandel (verkoop aan andere ondernemingen, niet zelf vervaardigd)'
        )
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_landbouw",
            sql="""
SELECT * FROM hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group in (
        'teelt eenjarige gewassen',
        'gemengd bedrijf',
        'teelt sierplanten',
        'dienstverlening voor de land/tuinbouw',
        'teelt meerjarige gewassen',
        'fokken, houden dieren')
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_persoonlijke_dienstverlening",
            sql="""
SELECT * FROM hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group in (
        'sauna, solaria',
        'schoonheidsverzorging',
        'uitvaart, crematoria',
        'overige dienstverlening',
        'kappers')
"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_informatie_telecommunicatie",
            sql="""
SELECT * FROM hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group in (
    'activiteiten op het gebied van ict',
    'activiteiten  op gebied van film, tv, radio, audio',
    'telecommunicatie',
    'uitgeverijen')
"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_cultuur_sport_recreatie",
            sql="""
SELECT * FROM hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group in (
        'sport',
        'musea, bibliotheken, kunstuitleen',
        'kunst',
        'recreatie')
"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_financiele_dienstverlening_verhuur",
            sql="""
SELECT * FROM hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group in (
        'verhuur van- en beheer/handel in onroerend goed',
        'verhuur van roerende goederen',
        'holdings',
        'financiële dienstverlening en verzekeringen')
"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_overige",
            sql="""
SELECT * FROM hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group in (
    'idieële organisaties',
    'belangenorganisaties',
    'overige',
    'hobbyclubs')
"""
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_horeca",
            sql="""
SELECT * FROM hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group in (
    'hotel-restaurant',
    'overige horeca',
    'kantine, catering',
    'cafetaria, snackbar, ijssalon',
    'café',
    'hotel, pension',
    'restaurant, café-restaurant')
"""
        ),

    ]
