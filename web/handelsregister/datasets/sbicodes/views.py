"""
SBI dataset gebruikt door HR.
"""

from datapunt_api import rest
from . import models
from . import serializers


# from django_filters.rest_framework import filters
# from django_filters.rest_framework import FilterSet


class SBIViewSet(rest.AtlasViewSet):
    """
    opgeschoonde SBI codes van het CBS die gebruikt worden door HR
    """

    queryset = models.SBICodeHierarchy.objects.all()
    queryset_detail = models.SBICodeHierarchy.objects.all()

    serializer_detail_class = serializers.SBICodeHierarchyDetailsSerializer
    serializer_class = serializers.SBICodeHierarchySerializer

    ordering = ('id',)
