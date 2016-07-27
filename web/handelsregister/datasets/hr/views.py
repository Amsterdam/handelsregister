# Create your views here.

from datapunt import rest

from . import models
from . import serializers


class MaatschappelijkeActiviteitViewSet(rest.AtlasViewSet):

    queryset = models.MaatschappelijkeActiviteit.objects.all()

    serializer_detail_class = serializers.MaatschappelijkeActiviteit
    serializer_class = serializers.MaatschappelijkeActiviteit

    def retrieve(self, request, *args, **kwargs):

        return super().retrieve(
            request, *args, **kwargs)


class PersoonViewSet(rest.AtlasViewSet):

    queryset = models.Persoon.objects.all()

    serializer_detail_class = serializers.Persoon
    serializer_class = serializers.Persoon

    def retrieve(self, request, *args, **kwargs):

        return super().retrieve(
            request, *args, **kwargs)
