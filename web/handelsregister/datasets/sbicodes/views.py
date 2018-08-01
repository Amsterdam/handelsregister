"""
SBI dataset gebruikt door HR.
"""

from datapunt_api import rest
from . import models
from . import serializers


# from django_filters.rest_framework import filters
# from django_filters.rest_framework import FilterSet


class SBIViewSet(rest.DatapuntViewSet):
    """
    opgeschoonde SBI codes van het CBS die gebruikt worden door HR
    """

    queryset = models.SBICodeHierarchy.objects.all()
    queryset_detail = models.SBICodeHierarchy.objects.all()

    serializer_detail_class = serializers.SBICodeHierarchyDetailsSerializer
    serializer_class = serializers.SBICodeHierarchySerializer

    detailed_keyword = 'detailed'

    def list(self, request, *args, **kwargs):
        # Checking if a detailed response is required
        if request.GET.get(self.detailed_keyword, False):
            self.serializer_class = self.serializer_detail_class
        return super().list(request, *args, **kwargs)

    ordering = ('id',)
