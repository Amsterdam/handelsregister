# Create your views here.

from datapunt import rest

from . import models
from . import serializers


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

    serializer_detail_class = serializers.Persoon
    serializer_class = serializers.Persoon


class VestigingViewSet(rest.AtlasViewSet):
    """
    Vestiging (VES)

    Een Vestiging is gebouw of een complex van gebouwen waar duurzame
    uitoefening van activiteiten van een Onderneming of Rechtspersoon
    plaatsvindt. De vestiging is een combinatie van Activiteiten en
    Locatie.
    """

    queryset = models.Vestiging.objects.all()

    serializer_detail_class = serializers.VestigingDetail
    serializer_class = serializers.Vestiging

    filter_fields = ('maatschappelijke_activiteit',)


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
