# Create your views here.

from datapunt import rest

from . import models
from . import serializers


class MaatschappelijkeActiviteitViewSet(rest.AtlasViewSet):
    """
    Maatschappelijke Activiteit

    Een maatschappelijke activiteit (MAC) is
    is de activiteit van een {Natuurlijk persoon}
    of {Niet-natuurlijk persoon}.

    De {Maatschappelijke Activiteit} is het totaal van
    alle activiteiten uitgeoefend door een {Natuurlijk Persoon}
    of een {Niet-natuurlijk Persoon}.
    Een {Maatschappelijke Activiteit} kan ook als {Onderneming}
    voorkomen.

    [Stelselpedia](https://www.amsterdam.nl/stelselpedia/hr-index/catalogus/maatschappelijke/)

    """

    queryset = models.MaatschappelijkeActiviteit.objects.all()

    # queryset_detail = models.MaatschappelijkeActiviteit.objects.select_related(
    # )

    serializer_detail_class = serializers.MaatschappelijkeActiviteit
    serializer_class = serializers.MaatschappelijkeActiviteit

    filter_fields = ('naam', 'kvknummer', 'macid')

    def retrieve(self, request, *args, **kwargs):
        """
        retrieve MaatschappelijkeActiviteit Details

        ---

        serializer: serializers.MaatschappelijkeActiviteit

        """

        return super().retrieve(
            request, *args, **kwargs)
