from rest_framework import serializers

from datapunt import rest
from . import models

from rest_framework.reverse import reverse


class Communicatiegegevens(serializers.ModelSerializer):
    class Meta(object):
        model = models.Communicatiegegevens
        exclude = (
            'id',
        )


class Handelsnaam(serializers.ModelSerializer):
    class Meta(object):
        model = models.Handelsnaam
        exclude = (
            'id',
        )


class Onderneming(serializers.ModelSerializer):
    handelsnamen = Handelsnaam(many=True)

    class Meta(object):
        model = models.Onderneming
        exclude = (
            'id',
        )


class Locatie(serializers.ModelSerializer):
    class Meta(object):
        model = models.Locatie
        exclude = (
            'id',
        )


class CommercieleVestiging(serializers.ModelSerializer):
    class Meta(object):
        model = models.CommercieleVestiging
        exclude = (
            'id',
        )


class NietCommercieleVestiging(serializers.ModelSerializer):
    class Meta(object):
        model = models.NietCommercieleVestiging
        exclude = (
            'id',
        )


class Activiteit(serializers.ModelSerializer):
    class Meta(object):
        model = models.Activiteit
        exclude = (
            'id',
        )


class MaatschappelijkeActiviteit(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()

    class Meta(object):
        model = models.MaatschappelijkeActiviteit
        lookup_field = 'kvk_nummer'

        extra_kwargs = {
            '_links': {'lookup_field': 'kvk_nummer'}
        }

        fields = (
            '_links',
            'kvk_nummer',
            '_display',
        )


class BijzondereRechtsToestand(serializers.ModelSerializer):

        class Meta(object):
            model = models.Persoon

            fields = (
                'faillissement',
            )


class MaatschappelijkeActiviteitDetail(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()
    onderneming = Onderneming()
    communicatiegegevens = Communicatiegegevens(many=True)
    postadres = Locatie()
    bezoekadres = Locatie()
    vestigingen = rest.RelatedSummaryField()

    _bijzondere_rechts_toestand = BijzondereRechtsToestand(source='eigenaar')

    class Meta(object):
        model = models.MaatschappelijkeActiviteit
        lookup_field = 'kvk_nummer'

        extra_kwargs = {
            '_links': {'lookup_field': 'kvk_nummer'},
            'hoofdvestiging': {'lookup_field': 'vestigingsnummer'},
        }

        fields = (
            '_links',
            '_display',
            'onderneming',
            'communicatiegegevens',
            'postadres',
            'bezoekadres',
            'vestigingen',
            'naam',
            'kvk_nummer',
            'datum_aanvang',
            'datum_einde',
            'incidenteel_uitlenen_arbeidskrachten',
            'non_mailing',
            'eigenaar_mks_id',
            'eigenaar',
            'hoofdvestiging',
            'activiteiten',
            '_bijzondere_rechts_toestand'
        )


class Persoon(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()

    class Meta(object):
        model = models.Persoon

        fields = (
            '_links',
            'id',
            '_display',
        )


class NatuurlijkPersoon(serializers.ModelSerializer):

    class Meta(object):
        model = models.NatuurlijkPersoon

        exclude = (
            'id',
        )


class NietNatuurlijkPersoon(serializers.ModelSerializer):

    class Meta(object):
        model = models.NietNatuurlijkPersoon

        exclude = (
            'id',
        )


class PersoonDetail(rest.HALSerializer):
    # dataset = 'hr'

    natuurlijkpersoon = NatuurlijkPersoon()
    niet_natuurlijkpersoon = NietNatuurlijkPersoon()

    maatschappelijke_activiteit = serializers.SerializerMethodField()
    heeft_aansprakelijke = rest.RelatedSummaryField()
    is_aansprakelijke = rest.RelatedSummaryField()

    _display = rest.DisplayField()

    class Meta(object):
        model = models.Persoon

        fields = (
            'id',
            '_display',
            'natuurlijkpersoon',
            'niet_natuurlijkpersoon',
            'maatschappelijke_activiteit',

            'is_aansprakelijke',
            'heeft_aansprakelijke',

            'rol',
            'rechtsvorm',
            'uitgebreide_rechtsvorm',
            'volledige_naam',
            'typering',
            'reden_insolvatie',
            'datum_aanvang',
            'datum_einde',
            'soort',
            'datumuitschrijving',
            'nummer',
            'toegangscode',
            'faillissement',
        )

    def get_maatschappelijke_activiteit(self, obj):
        if obj.rol == 'EIGENAAR':
            mac = models.MaatschappelijkeActiviteit.objects.get(
                eigenaar=obj.id)
            url = reverse(
                'maatschappelijkeactiviteit-detail',
                request=self.context['request'],
                args=[str(mac.kvk_nummer)])
            return url


class VestigingLocatie(serializers.ModelSerializer):
    class Meta(object):
        model = models.Locatie
        fields = (
            'straatnaam',
            'postcode',
            'toevoegingadres',
        )
class Vestiging(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()
    straatnaam = serializers.SlugRelatedField()

    class Meta(object):
        model = models.Vestiging
        lookup_field = 'vestigingsnummer'
        extra_kwargs = {
            '_links': {'lookup_field': 'vestigingsnummer'}
        }

        fields = (
            '_links',
            '_display',
            'naam',
        )


class VestigingDetail(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()
    commerciele_vestiging = CommercieleVestiging()
    niet_commerciele_vestiging = NietCommercieleVestiging()
    communicatiegegevens = Communicatiegegevens(many=True)
    postadres = Locatie()
    bezoekadres = Locatie()
    activiteiten = Activiteit(many=True)
    handelsnamen = Handelsnaam(many=True)

    class Meta(object):
        model = models.Vestiging
        lookup_field = 'vestigingsnummer'
        extra_kwargs = {
            '_links': {'lookup_field': 'vestigingsnummer'},
            'maatschappelijke_activiteit': {'lookup_field': 'kvk_nummer'},
        }
        fields = '__all__'


class Functievervulling(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()

    class Meta(object):
        model = models.Functievervulling

        fields = (
            '_links',
            '_display',
        )


class FunctievervullingDetail(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()

    class Meta(object):
        model = models.Functievervulling
        fields = '__all__'
