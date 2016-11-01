
from django.db import migrations
from geo_views import migrate
from django.conf import settings
from django.contrib.sites.models import Site


def create_site(apps, *args, **kwargs):
    pass

def delete_site(apps, *args, **kwargs):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('geo_views', '__first__'),
        ('geo_views', '0001_vestigingen_views'),
    ]

    operations = [
        # set the site name
        # migrations.RunPython(code=create_site, reverse_code=delete_site),
        # create the hr views
        migrate.ManageView(
            view_name="geo_hr_vestiging_locaties_persoonlijke_dienstverlening_naam",
            sql="""
SELECT row_number() OVER () AS id, geometrie, naam
from hr_geovestigingen
WHERE hr_geovestigingen.sbi_detail_group in (
        'sauna, solaria',
        'schoonheidsverzorging',
        'uitvaart, crematoria',
        'overige dienstverlening',
        'kappers')
        GROUP BY geometrie, naam
    """)]