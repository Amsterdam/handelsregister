
from rest_framework import serializers

from datapunt import rest

from . import models


class Communicatiegegevens(serializers.ModelSerializer):
    dataset = 'hr'

    class Meta:
        model = models.Communicatiegegevens


class MaatschappelijkeActiviteit(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()
    communicatiegegevens = Communicatiegegevens()

    class Meta:
        model = models.MaatschappelijkeActiviteit


class Persoon(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()

    class Meta:
        model = models.Persoon


class Vestiging(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()

    class Meta:
        model = models.Vestiging


class Functievervulling(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()

    class Meta:
        model = models.Functievervulling
