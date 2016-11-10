"""
Elasticsearch index document defenitions
"""
import logging
# import json

from django.conf import settings

from search import analyzers

import elasticsearch_dsl as es

from datasets.hr import models

log = logging.getLogger(__name__)


def get_centroid(geom, transform=None):
    """
    Finds the centroid of a geometrie object
    An optional transform string can be given noting
    the name of the system to translate to, i.e. 'wgs84'
    """
    if not geom:
        return None

    result = geom.centroid
    if transform:
        result.transform(transform)
    return result.coords


class MaatschappelijkeActiviteit(es.DocType):

    _display = es.String(index='not_analyzed')

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

    handelsnamen = es.Nested({
        'properties': {
            'naam': es.String(
                analyzer=analyzers.adres,
                fields={
                    'raw': es.String(index='not_analyzed'),
                    'ngram': es.String(
                        analyzer=analyzers.autocomplete,
                        search_analyzer='standard')
                })
            }
    })

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

    centroid = es.GeoPoint()

    class Meta:
        index = settings.ELASTIC_INDICES['HR']
        all = es.MetaField(enabled=False)


class Vestiging(es.DocType):

    _display = es.String(index='not_analyzed')

    vestigingsnummer = es.String(
        analyzer=analyzers.autocomplete,
        fields={
            'raw': es.String(index='not_analyzed')}
    )

    hoofdvestiging = es.Boolean()

    sbi = es.Nested({
        'properties': {
            'code': es.String(
                analyzer=analyzers.autocomplete,
                fields={
                    'raw': es.String(index='not_analyzed')}
            ),
            'omschrijving': es.String(),
            }
        })

    naam = es.String(
        analyzer=analyzers.adres,
        fields={
            'raw': es.String(index='not_analyzed'),
            'ngram': es.String(
                analyzer=analyzers.autocomplete,
                search_analyzer='standard')}
        )

    handelsnamen = es.Nested({
        'properties': {
            'naam': es.String(
                analyzer=analyzers.adres,
                fields={
                    'raw': es.String(index='not_analyzed'),
                    'ngram': es.String(
                        analyzer=analyzers.autocomplete,
                        search_analyzer='standard')
                })
            }
    })

    postadres = es.String(
        analyzer=analyzers.adres,
        fields={
            'raw': es.String(index='not_analyzed'),
            'ngram': es.String(
                analyzer=analyzers.autocomplete,
                search_analyzer='standard')})

    bezoekadres = es.String(
        analyzer=analyzers.adres,
        fields={
            'raw': es.String(index='not_analyzed'),
            'ngram': es.String(
                analyzer=analyzers.autocomplete,
                search_analyzer='standard')})

    centroid = es.GeoPoint()

    class Meta:
        index = settings.ELASTIC_INDICES['HR']
        all = es.MetaField(enabled=False)


def from_mac(mac: models.MaatschappelijkeActiviteit):
    """
    Create doc from mac
    """
    doc = MaatschappelijkeActiviteit(_id=mac.id)

    doc._display = str(mac)

    doc.naam = mac.naam
    doc.kvk_nummer = mac.kvk_nummer

    if mac.onderneming:
        for h in mac.onderneming.handelsnamen.all():
            doc.handelsnamen.append(dict(
                naam=h.handelsnaam))

    if mac.bezoekadres:
        doc.bezoekadres = mac.bezoekadres.volledig_adres
        doc.centroid = get_centroid(mac.bezoekadres.geometrie, 'wgs84')
    if mac.postadres:
        doc.postadres = mac.postadres.volledig_adres

    # logging.error(json.dumps(doc.to_dict(), indent=4))
    return doc


def from_vestiging(ves: models.Vestiging):
    """
    Create a doc from a vestiging
    """

    doc = Vestiging(_id=ves.id)

    doc._display = str(ves)

    doc.vestigingsnummer = ves.vestigingsnummer
    doc.hoofdvestiging = ves.hoofdvestiging

    doc.naam = ves.naam

    for h in ves.handelsnamen.all():
        doc.handelsnamen.append(dict(
            naam=h.handelsnaam))

    for act in ves.activiteiten.all():
        doc.sbi.append(dict(
            code=act.sbi_code, omschrijving=act.sbi_omschrijving))

    if ves.bezoekadres:
        doc.bezoekadres = ves.bezoekadres.volledig_adres
        doc.centroid = get_centroid(ves.bezoekadres.geometrie, 'wgs84')
    if ves.postadres:
        doc.postadres = ves.bezoekadres.volledig_adres

    # logging.error(json.dumps(doc.to_dict(), indent=4))

    return doc
