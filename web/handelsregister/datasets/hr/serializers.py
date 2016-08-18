from rest_framework import fields
from rest_framework import serializers

from datapunt import rest
from . import models


class Communicatiegegevens(serializers.ModelSerializer):
    dataset = 'hr'

    class Meta:
        model = models.Communicatiegegevens
        exclude = (
            'id',
        )


class Onderneming(serializers.ModelSerializer):
    dataset = 'hr'

    class Meta:
        model = models.Onderneming
        exclude = (
            'id',
        )


class Locatie(serializers.ModelSerializer):
    dataset = 'hr'

    class Meta:
        model = models.Locatie
        exclude = (
            'id',
        )


class MaatschappelijkeActiviteit(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()

    class Meta:
        model = models.MaatschappelijkeActiviteit
        fields = (
            '_links',
            'kvk_nummer',
            '_display',
        )


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


class MaatschappelijkeActiviteitDetail(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()
    onderneming = Onderneming()
    communicatiegegevens = Communicatiegegevens(many=True)
    postadres = Locatie()
    bezoekadres = Locatie()

    class Meta:
        model = models.MaatschappelijkeActiviteit
