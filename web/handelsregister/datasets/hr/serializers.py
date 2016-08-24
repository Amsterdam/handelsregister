from rest_framework import fields
from rest_framework import relations
from rest_framework import serializers

from datapunt import rest
from . import models


class Communicatiegegevens(serializers.ModelSerializer):
    class Meta:
        model = models.Communicatiegegevens
        exclude = (
            'id',
        )


class Onderneming(serializers.ModelSerializer):
    class Meta:
        model = models.Onderneming
        exclude = (
            'id',
        )


class Locatie(serializers.ModelSerializer):
    class Meta:
        model = models.Locatie
        exclude = (
            'id',
        )

class CommercieleVestiging(serializers.ModelSerializer):
    class Meta:
        model = models.CommercieleVestiging
        exclude = (
            'id',
        )

class NietCommercieleVestiging(serializers.ModelSerializer):
    class Meta:
        model = models.NietCommercieleVestiging
        exclude = (
            'id',
        )

class Activiteit(serializers.ModelSerializer):
    class Meta:
        model = models.Activiteit
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
        fields = (
            '_links',
            '_display',
        )


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
    vestigingen = rest.RelatedSummaryField()

    class Meta:
        model = models.MaatschappelijkeActiviteit


class VestigingDetail(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()
    commerciele_vestiging = CommercieleVestiging()
    niet_commerciele_vestiging = NietCommercieleVestiging()
    communicatiegegevens = Communicatiegegevens(many=True)
    postadres = Locatie()
    bezoekadres = Locatie()
    activiteiten = Activiteit(many=True)

    class Meta:
        model = models.Vestiging

    def to_representation(self, instance):
        return super().to_representation(instance)

