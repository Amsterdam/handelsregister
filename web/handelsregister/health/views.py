import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
try:
    from django.apps import apps
    get_model = apps.get_model
except ImportError:
    from django.db.models.loading import get_model

from django.http import HttpResponse

try:
    model = get_model(settings.HEALTH_MODEL)
except:
    raise ImproperlyConfigured(
        'settings.HEALTH_MODEL doesn\'t resolve to a useable model')


log = logging.getLogger(__name__)


def health(request):
    # check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("select 1")
            assert cursor.fetchone()
    except:
        log.exception("Database connectivity failed")
        return HttpResponse(
            "Database connectivity failed",
            content_type="text/plain", status=500)

    # check debug
    if settings.DEBUG:
        log.exception("Debug mode not allowed in production")
        return HttpResponse(
            "Debug mode not allowed in production",
            content_type="text/plain", status=500)

    return HttpResponse("Health OK", content_type='text/plain', status=200)


def check_data(request):
    # check bag
    try:
        assert model.objects.count() > 1000
    except:
        log.exception("No HR data found")
        return HttpResponse(
            "No HR data found",
            content_type="text/plain", status=500)

    # check geoviews data
    try:
        assert model.objects.count() > 1000
    except:
        log.exception("No HR data found")
        return HttpResponse(
            "No HR data found",
            content_type="text/plain", status=500)

    return HttpResponse("Data OK", content_type='text/plain', status=200)
