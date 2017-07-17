# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from geo_views import migrate

geovestigingen_template = """
SELECT * FROM hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group IN (SELECT subcategorie FROM hr_cbs_sbi_subcat WHERE hcat_id IN (
    SELECT hcat FROM hr_cbs_sbi_hoofdcat WHERE hoofdcategorie = '{}'
))
"""

geovestigingen_naamquery_template = """
SELECT row_number() OVER () AS id, geometrie, naam, locatie_type
from hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group IN (SELECT subcategorie FROM hr_cbs_sbi_subcat WHERE hcat_id IN (
    SELECT hcat FROM hr_cbs_sbi_hoofdcat WHERE hoofdcategorie = '{}'
))
GROUP BY geometrie, naam, locatie_type
"""


class Migration(migrations.Migration):
    dependencies = [
        ('geo_views', '0001_vestigingen_views'),
        ('hr', '0020_extra_sbicodes'),
    ]

    operations = [
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_bouw",
            sql=geovestigingen_template.format("bouw")
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_overheid_onderwijs_zorg",
            sql=geovestigingen_template.format("overheid, onderwijs, zorg")
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_productie_installatie_reparatie",
            sql=geovestigingen_template.format("productie, installatie, reparatie")
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_zakelijke_dienstverlening",
            sql=geovestigingen_template.format("zakelijke dienstverlening")
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_handel_vervoer_opslag",
            sql=geovestigingen_template.format("handel, vervoer, opslag")
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_landbouw",
            sql=geovestigingen_template.format("landbouw")
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_persoonlijke_dienstverlening",
            sql=geovestigingen_template.format("persoonlijke dienstverlening")
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_informatie_telecommunicatie",
            sql=geovestigingen_template.format("informatie, telecommunicatie")
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_cultuur_sport_recreatie",
            sql=geovestigingen_template.format("cultuur, sport, recreatie")
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_financiele_dienstverlening_verhuur",
            sql=geovestigingen_template.format("financiële dienstverlening,verhuur van roerend en onroerend goed")
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_overige",
            sql=geovestigingen_template.format("overige niet hierboven genoemd")
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_horeca",
            sql=geovestigingen_template.format("horeca")
        ),

        # NAAM QUERIES / LABELS mapserver
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_bouw_naam",
            sql=geovestigingen_naamquery_template.format("bouw")
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_overheid_onderwijs_zorg_naam",
            sql=geovestigingen_naamquery_template.format("overheid, onderwijs, zorg")
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_productie_installatie_reparatie_naam",
            sql=geovestigingen_naamquery_template.format("productie, installatie, reparatie")
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_zakelijke_dienstverlening_naam",
            sql=geovestigingen_naamquery_template.format("zakelijke dienstverlening")
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_handel_vervoer_opslag_naam",
            sql=geovestigingen_naamquery_template.format("handel, vervoer, opslag")
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_landbouw_naam",
            sql=geovestigingen_naamquery_template.format("landbouw")
        ),

        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_persoonlijke_dienstverlening_naam",
            sql=geovestigingen_naamquery_template.format("persoonlijke dienstverlening")
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_informatie_telecommunicatie_naam",
            sql=geovestigingen_naamquery_template.format("informatie, telecommunicatie")
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_cultuur_sport_recreatie_naam",
            sql=geovestigingen_naamquery_template.format("cultuur, sport, recreatie")
        ),
        # Note afwijkende naam ivm. maximale lengte
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_financiele_dienstverlening_verhuur_na",
            sql=geovestigingen_naamquery_template.format("financiële dienstverlening,verhuur van roerend en onroerend goed")
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_overige_naam",
            sql=geovestigingen_naamquery_template.format("overige niet hierboven genoemd")
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_horeca_naam",
            sql=geovestigingen_naamquery_template.format("horeca")
        ),
    ]
