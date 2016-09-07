# Create your views here.

from datapunt import rest

from django_filters import MethodFilter

from django.db.models import Q

from rest_framework import filters

from . import models
from . import serializers

import requests


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

    filter_fields = ('eigenaar', 'naam')


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

    filter_fields = (
        'typering', 'naam', 'soort',
        'niet_natuurlijkpersoon__rsin')


class VestigingFilter(filters.FilterSet):
    """
    Filter on nummeraanduiging and vestigingid
    """

    nummeraanduiding = MethodFilter(action='nummeraanduiding_filter')
    verblijfsobject = MethodFilter(action='verblijfsobject_filter')
    pand = MethodFilter(action='pand_filter')

    class Meta:
        model = models.Vestiging

        fields = (
            'maatschappelijke_activiteit',
            'nummeraanduiding',
            'verblijfsobject',
            'bezoekadres__bag_numid')

        order_by = ['naam']

    def nummeraanduiding_filter(self, queryset, value):
        """
        Filter Vestiging op nummeraanduiding
        """

        return queryset.filter(
            Q(bezoekadres__bag_numid=value) |
            Q(postadres__bag_numid=value))

    def verblijfsobject_filter(self, queryset, value):
        """
        Filter Vestiging op verblijfsobject
        """

        return queryset.filter(
            Q(bezoekadres__bag_vbid=value) |
            Q(postadres__bag_vbid=value))

    def collect_landelijke_ids(self, vbo_ids, value, page):
        params = {
            'panden__id': value,
            'page': page
        }

        response = requests.get(
            'https://api.datapunt.amsterdam.nl/bag/verblijfsobject/', params)

        data = response.json()

        for vbo in data.get('results', []):
            vbo_ids.append(vbo['landelijk_id'])

        if not data:
            return False
        if not data.get('_links'):
            return False

        return data['_links'].get('next', False)

    def pand_filter(self, queryset, value):
        """
        Given a pand id pick up all verblijfsobjecten
        and find all vestigingen.
        """

        vbo_ids = []
        more_data = True
        page = 0

        while more_data:
            page += 1
            more_data = self.collect_landelijke_ids(vbo_ids, value, page)

        return queryset.filter(
            Q(bezoekadres__bag_vbid__in=vbo_ids) |
            Q(postadres__bag_vbid__in=vbo_ids))


class VestigingViewSet(rest.AtlasViewSet):
    """
    Vestiging (VES)

    Een Vestiging is gebouw of een complex van gebouwen waar duurzame
    uitoefening van activiteiten van een Onderneming of Rechtspersoon
    plaatsvindt. De vestiging is een combinatie van Activiteiten en
    Locatie.

    filtering is possible on:

        maatschappelijke_activiteit
        nummeraanduiding
        verblijfsobject
        bezoekadres__bag_numid
        pand

    example:

    https://api-acc.datapunt.amsterdam.nl/handelsregister/vestiging/?pand=03630013105220

    """

    queryset = models.Vestiging.objects.all()

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

    ordering_fields = ('naam',)

    filter_class = VestigingFilter


class FunctievervullingViewSet(rest.AtlasViewSet):
    """
    Functievervulling (FVV)

    Een Functievervulling is een vervulling door een Persoon van een functie
    voor een Persoon. Een Functievervulling geeft de relatie weer van de
    Persoon als functionaris en de Persoon als eigenaar van de
    Onderneming of MaatschappelijkeActiviteit.
    """

    queryset = models.Functievervulling.objects.all()

    serializer_detail_class = serializers.Functievervulling
    serializer_class = serializers.Functievervulling
