
from django.db import migrations
from geo_views import migrate
from django.conf import settings
from django.contrib.sites.models import Site


class Migration(migrations.Migration):
    dependencies = [
        ('hr', '0007_dataselectie'),
    ]

    # moved code to views ...
    operations = []
