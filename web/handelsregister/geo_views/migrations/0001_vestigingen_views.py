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
            sql="""
SELECT
  ROW_NUMBER() OVER (ORDER BY vs.id ASC) AS id,
  vs.vestigingsnummer as display,
  CAST(a.sbi_code AS INTEGER),
  a.activiteitsomschrijving,
  vs.naam,
  vs.hoofdvestiging,
  CASE vs.bezoekadres_id
    WHEN null THEN true
    ELSE false
  END as is_bezoekadres,
  loc.geometry as geometrie,
  CAST('handelsregister/vestiging' AS text),
  site.domain || 'handelsregister/vestiging/' || vs.vestigingsnummer || '/' AS uri
FROM hr_vestiging_activiteiten hr_a
    JOIN hr_vestiging vs
    ON hr_a.vestiging_id = vs.id
    JOIN hr_activiteit a
    ON a.id = hr_a.activiteit_id
    JOIN hr_locatie loc
    ON (vs.bezoekadres_id = loc.id
        OR vs.postadres_id = loc.id
        AND ST_IsValid(loc.geometry)),
    django_site site
WHERE loc.geometry != '' AND site.name = 'API Domain'
ORDER BY vs.id
"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_horeca",
            sql="""
SELECT * FROM geo_hr_vestiging_locaties
WHERE sbi_code between 561 and 564 OR
      sbi_code between 5610 and 5640 OR
      sbi_code between 56100 and 56400"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_hotels",
            sql="""
        SELECT * FROM geo_hr_vestiging_locaties
        WHERE sbi_code between 551 and 553 OR
              sbi_code between 5510 and 5530 OR
              sbi_code between 55100 and 55300 OR
              sbi_code = 559 OR sbi_code = 5590"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_onderwijs",
            sql="""
    SELECT * FROM geo_hr_vestiging_locaties
    WHERE sbi_code between 852 and 856 OR
          sbi_code between 8520 and 8560 OR
          sbi_code between 85200 and 85600"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_kinderopvang",
            sql="""
    SELECT * FROM geo_hr_vestiging_locaties
    WHERE sbi_code = 8891 OR
          sbi_code between 88911 and 88912"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_cultuur",
            sql="""
        SELECT * FROM geo_hr_vestiging_locaties
        WHERE sbi_code = 900 OR
              sbi_code between 9000 and 9109 OR
              sbi_code between 90000 and 91090"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_religies",
            sql="""
        SELECT * FROM geo_hr_vestiging_locaties
        WHERE sbi_code >= 94911 and sbi_code <= 94920"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_sport",
            sql="""
    SELECT * FROM geo_hr_vestiging_locaties
    WHERE sbi_code = 931 OR
          (sbi_code >= 9310 and sbi_code < 9320) OR
          (sbi_code >= 93100 and sbi_code < 93200)"""
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_zorg",
            sql="""
    SELECT * FROM geo_hr_vestiging_locaties
    WHERE
          sbi_code between 861 AND 882 OR
          sbi_code between 8610 AND 8820 OR
          sbi_code between 86100 and 88200 OR
          sbi_code between 88911 and 88912 OR
          sbi_code = 8899 OR
          sbi_code = 88991
          """
        ),
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_gemeente",
            sql="""
        SELECT * FROM geo_hr_vestiging_locaties
        WHERE sbi_code = 68202 OR
        (sbi_code >= 841 and sbi_code <= 842) OR
        (sbi_code  >= 8420 and sbi_code <= 8430)
        """
        ),

    ]
