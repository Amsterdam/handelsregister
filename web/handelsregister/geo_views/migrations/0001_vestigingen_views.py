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
  a.sbi_code,
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
    ]
