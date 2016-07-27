
from rest_framework import serializers

from datapunt import rest

from . import models


class CommunicatieGegevens(serializers.ModelSerializer):
    dataset = 'hr'

    class Meta:
        model = models.CommunicatieGegevens


class MaatschappelijkeActiviteit(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()
    communicatiegegevens = CommunicatieGegevens()

    class Meta:
        model = models.MaatschappelijkeActiviteit


class Persoon(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()

    class Meta:
        model = models.Persoon
