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
    dependencies = []

    operations = [
        # set the site name
        migrations.RunPython(code=create_site, reverse_code=delete_site),
        # create the hr views
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties",
            sql="""
SELECT
  vs.id,
  vs.id as display,
  a.sbi_code,
  a.activiteitsomschrijving,
  vs.naam,
  loc.geometry as geometrie,
  'handelsregister/vestiging' AS type,
  site.domain || 'handelsregister/vestiging/' || vs.id || '/' AS uri
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
