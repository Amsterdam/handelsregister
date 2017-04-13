# Create your views here.

import logging

import requests
from django.conf import settings
# from django_filters import Filter

from django_filters.rest_framework import filters
from django_filters.rest_framework import FilterSet

from datapunt import rest
from . import models
from . import serializers

log = logging.getLogger(__name__)


class MacFilter(FilterSet):

    naam = filters.CharFilter()
    eigenaar = filters.CharFilter()

    class Meta:
        model = models.MaatschappelijkeActiviteit

        fields = (
            'eigenaar',
            'naam'
        )

    ordering = ('id',)


class MaatschappelijkeActiviteitViewSet(rest.AtlasViewSet):
    """
    Maatschappelijke Activiteit (MAC)

    Een MaatschappelijkeActiviteit is de activiteit van een
    NatuurlijkPersoon of NietNatuurlijkPersoon. De
    MaatschappelijkeActiviteit is het totaal van alle activiteiten
    uitgeoefend door een NatuurlijkPersoon of een NietNatuurlijkPersoon.
    Een MaatschappelijkeActiviteit kan ook als Onderneming voorkomen.
    """

    queryset = (models.MaatschappelijkeActiviteit.objects.all())
    queryset_detail = (models.MaatschappelijkeActiviteit.objects
                       .select_related('onderneming')
                       .select_related('hoofdvestiging')
                       .all())

    serializer_detail_class = serializers.MaatschappelijkeActiviteitDetail
    serializer_class = serializers.MaatschappelijkeActiviteit

    lookup_field = 'kvk_nummer'

    filter_fields = ('eigenaar', 'naam', 'bezoekadres__correctie')

    filter_class = MacFilter

    ordering = ('naam',)


class PersoonFilter(FilterSet):

    niet_natuurlijkpersoon__rsin = filters.CharFilter()
    naam = filters.CharFilter()

    class Meta:
        model = models.Persoon

        fields = (
            'typering',
            'naam',
            'soort',
            'niet_natuurlijkpersoon__rsin')

    ordering = ('naam',)


class PersoonViewSet(rest.AtlasViewSet):
    """
    Persoon (PRS)

    Een Persoon is een ieder die rechten en plichten kan hebben. Persoon
    wordt gebruikt als overkoepelend begrip (een verzamelnaam voor
    NatuurlijkPersoon, NietNatuurlijkPersoon en NaamPersoon) om er over
    te kunnen communiceren. Iedere in het handelsregister voorkomende Persoon
    heeft ofwel een Eigenaarschap en/ of minstens één Functievervulling
    waarmee de rol van de Persoon is vastgelegd.
    """

    queryset = models.Persoon.objects.all()

    queryset_detail = (models.Persoon.objects
                       .select_related('natuurlijkpersoon')
                       .select_related('niet_natuurlijkpersoon')
                       .all())

    serializer_detail_class = serializers.PersoonDetail

    serializer_class = serializers.Persoon
    filter_class = PersoonFilter

    ordering = ('id',)


class VestigingFilter(FilterSet):
    """
    Filter on nummeraanduiging and vestigingid
    """

    nummeraanduiding = filters.CharFilter(method='nummeraanduiding_filter')
    verblijfsobject = filters.CharFilter(method='verblijfsobject_filter')
    pand = filters.CharFilter(method='pand_filter')
    kadastraal_object = filters.CharFilter(method='kot_filter')

    bezoekadres__bag_numid = filters.CharFilter()
    maatschappelijke_activiteit = filters.CharFilter()

    class Meta:
        model = models.Vestiging

        fields = (
            'maatschappelijke_activiteit',
            'nummeraanduiding',
            'verblijfsobject',
            'bezoekadres__bag_numid',
            'bezoekadres__correctie'
        )

    def nummeraanduiding_filter(self, queryset, name, value):
        """
        Filter Vestiging op nummeraanduiding
        """

        locations = models.Locatie.objects.filter(bag_numid=value).values('id')

        q1 = queryset.filter(bezoekadres__in=locations)
        q2 = queryset.filter(postadres__in=locations)

        return q1 | q2

    def verblijfsobject_filter(self, queryset, name, value):
        """
        Filter Vestiging op verblijfsobject
        """
        locations = models.Locatie.objects.filter(bag_vbid=value).values('id')

        q1 = queryset.filter(bezoekadres__in=locations)
        q2 = queryset.filter(postadres__in=locations)

        return q1 | q2

    def _collect_landelijke_ids(self, filter_field, value):
        """
        Collect all 'landelijk_ids' for verblijfsobjecten given
        a filter_field (panden__landelijk_id, kadastrale_objecten__id)
        by doing a request to the bag api
        """

        vbo_ids = []
        more_data = True
        page = 0

        # more then 40 * 25 pages we will not show
        # just to spare our backend
        while more_data and page < 10:
            page += 1
            more_data = self._grab_vbo_page(vbo_ids, filter_field, value, page)

        return vbo_ids

    def _grab_vbo_page(self, vbo_ids, filter_field, value, page):
        """
        Grab a single filtered vbo page and retun True if there
        is more data
        """

        params = {'page': page, filter_field: value}

        url = settings.VBO_URI

        response = requests.get(url, params)

        data = response.json()

        for vbo in data.get('results', []):
            vbo_ids.append(vbo['landelijk_id'])

        stop = False
        get_more = True

        if not data:
            return stop
        if not data.get('_links'):
            return stop
        if not data['_links'].get('next'):
            return stop

        if data['_links']['next']['href'] is not None:
            return get_more

        return stop

    def pand_filter(self, queryset, name, value):
        """
        Given a pand id pick up all verblijfsobjecten
        and find all vestigingen.
        """
        # NOTE how to test this?
        vbo_ids = self._collect_landelijke_ids(
            'panden__landelijk_id', value)

        locations = models.Locatie.objects.filter(bag_vbid__in=vbo_ids)
        locations = locations.values('id')

        q1 = queryset.filter(bezoekadres__in=locations)
        q2 = queryset.filter(postadres__in=locations)

        return q1 | q2

    def kot_filter(self, queryset, name, value):
        """
        Given a kadastraal object find all
        """

        vbo_ids = self._collect_landelijke_ids(
            'kadastrale_objecten__id', value)

        locations = models.Locatie.objects.filter(
            bag_vbid__in=vbo_ids).values('id')

        q1 = queryset.filter(bezoekadres__in=locations)
        q2 = queryset.filter(postadres__in=locations)

        return q1 | q2


class VestigingViewSet(rest.AtlasViewSet):
    """
    Vestiging (VES)

    Een Vestiging is gebouw of een complex van gebouwen waar duurzame
    uitoefening van activiteiten van een Onderneming of Rechtspersoon
    plaatsvindt. De vestiging is een combinatie van Activiteiten en
    Locatie.

    Filteren is mogelijk op:

        maatschappelijke_activiteit
        nummeraanduiding
        verblijfsobject
        bezoekadres__bag_numid
        pand

    Zoeken op landelijk pand id van de Waag op de nieuwmarkt voorbeeld:

    [https://acc.api.data.amsterdam.nl/handelsregister/vestiging/?pand=0363100012171850](https://acc.api.data.amsterdam.nl/handelsregister/vestiging/?pand=0363100012171850)

    Zoeken op kadastraal object id voorbeeld:

    [https://acc.api.data.amsterdam.nl/handelsregister/vestiging/?kadastraal_object=NL.KAD.OnroerendeZaak.11450749270000](https://acc.api.data.amsterdam.nl/handelsregister/vestiging/?kadastraal_object=NL.KAD.OnroerendeZaak.11450749270000)
    """

    queryset = (models.Vestiging.objects
                .select_related('postadres')
                .select_related('bezoekadres')
                .all())

    queryset_detail = (models.Vestiging.objects
                       .select_related('maatschappelijke_activiteit')
                       .select_related('postadres')
                       .select_related('bezoekadres')
                       .select_related('commerciele_vestiging')
                       .select_related('niet_commerciele_vestiging')
                       .all())

    serializer_detail_class = serializers.VestigingDetail
    serializer_class = serializers.Vestiging

    lookup_field = 'vestigingsnummer'

    ordering_fields = '__all__'

    ordering = ('naam',)

    filter_class = VestigingFilter


class FunctievervullingFilter(FilterSet):

    heeft_aansprakelijke = filters.CharFilter()
    is_aansprakelijke = filters.CharFilter()

    class Meta:
        model = models.Functievervulling

        fields = (
            'heeft_aansprakelijke',
            'is_aansprakelijke'
        )

    ordering = ('id',)


class FunctievervullingViewSet(rest.AtlasViewSet):
    """
    Functievervulling (FVV)

    Een Functievervulling is een vervulling door een Persoon van een functie
    voor een Persoon. Een Functievervulling geeft de relatie weer van de
    Persoon als functionaris en de Persoon als eigenaar van de
    Onderneming of MaatschappelijkeActiviteit.
    """

    queryset = (models.Functievervulling.objects
                .select_related('is_aansprakelijke')
                .select_related('heeft_aansprakelijke'))

    serializer_detail_class = serializers.FunctievervullingDetail
    serializer_class = serializers.Functievervulling

    filter_class = FunctievervullingFilter

    ordering = ('id',)
