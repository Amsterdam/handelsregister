"""
Elasticsearch index document defenitions
"""
import logging

from django.conf import settings

from datasets.elk import analyzers

import elasticsearch_dsl as es

from datasets.hr import models

log = logging.getLogger(__name__)


class MaatschappelijkeActiviteit(es.DocType):

    kvk_nummer = es.String(
        analyzer=analyzers.autocomplete,
        fields={
            'raw': es.String(index='not_analyzed')}
    )

    naam = es.String(
        analyzer=analyzers.adres,
        fields={
            'raw': es.String(index='not_analyzed'),
            'ngram': es.String(
                analyzer=analyzers.autocomplete, search_analyzer='standard')})

    postadres = es.String(
        analyzer=analyzers.adres,
        fields={
            'raw': es.String(index='not_analyzed'),
            'ngram': es.String(
                analyzer=analyzers.autocomplete, search_analyzer='standard')})

    bezoekadres = es.String(
        analyzer=analyzers.adres,
        fields={
            'raw': es.String(index='not_analyzed'),
            'ngram': es.String(
                analyzer=analyzers.autocomplete, search_analyzer='standard')})

    # hoofdvestiging
    #

    centroid = es.GeoPoint()

    class Meta:
        index = settings.ELASTIC_INDICES['HR']
        all = es.MetaField(enabled=False)


def from_mac(m: models.MaatschappelijkeActiviteit):
    """
    Create doc from mac
    """
    d = MaatschappelijkeActiviteit(_id=m.id)

    d.naam = m.naam
    d.kvk_nummer = m.kvk_nummer

    if m.bezoekadres:
        d.bezoekadres = m.bezoekadres.volledig_adres
    if m.postadres:
        d.postadres = m.postadres.volledig_adres

    return d
