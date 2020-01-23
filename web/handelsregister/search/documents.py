"""
Elasticsearch index document defenitions
"""
import logging
import re

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


class Inschrijving(es.Document):

    _display = es.Keyword()

    _kvk_display = es.Keyword()

    doctype = es.Keyword()

    kvk_nummer = es.Text(
        analyzer=analyzers.autocomplete,
        fields={
            'raw': es.Keyword(),
            'nozero': es.Text(analyzer=analyzers.nozero)
        }
    )

    vestigingsnummer = es.Text(
        analyzer=analyzers.autocomplete,
        fields={
            'raw': es.Keyword(),
            'nozero': es.Text(analyzer=analyzers.nozero),
            'int': es.Integer()}
    )

    hoofdvestiging = es.Boolean()

    sbi = es.Nested(
        properties={
            'code': es.Text(
                analyzer=analyzers.autocomplete,
                fields={
                    'raw': es.Keyword()}
            ),
            'omschrijving': es.Text(),
            }
    )

    naam = es.Text(
        analyzer=analyzers.adres,
        fields={
            'raw': es.Keyword(),
            'ngram': es.Text(
                analyzer=analyzers.autocomplete,
                search_analyzer='standard')}
        )

    handelsnamen = es.Nested(
        properties={
            'naam': es.Text(
                analyzer=analyzers.adres,
                fields={
                    'raw': es.Keyword(),
                    'ngram': es.Text(
                        analyzer=analyzers.autocomplete,
                        search_analyzer='standard')
                })
            }
    )

    postadres = es.Text(
        analyzer=analyzers.adres,
        fields={
            'raw': es.Keyword(),
            'ngram': es.Text(
                analyzer=analyzers.autocomplete, search_analyzer='standard')})

    bezoekadres = es.Text(
        analyzer=analyzers.adres,
        fields={
            'raw': es.Keyword(),
            'ngram': es.Text(
                analyzer=analyzers.autocomplete, search_analyzer='standard')})

    bezoekadres_correctie = es.Boolean()

    # hoofdvestiging

    centroid = es.GeoPoint()

    class Index:
        name = settings.ELASTIC_INDICES['HR']


def from_mac(mac: models.MaatschappelijkeActiviteit):
    """
    Create doc from mac
    """
    doc = Inschrijving(_id=mac.id)

    doc.doctype = 'mac'

    doc._display = str(mac)  # pylint: disable=protected-access

    doc.naam = mac.naam
    doc.kvk_nummer = mac.kvk_nummer

    doc.handelsnamen.append(dict(naam=mac.naam))

    if mac.onderneming:
        for h in mac.onderneming.handelsnamen.all():
            doc.handelsnamen.append(dict(
                naam=h.handelsnaam))

    if mac.bezoekadres:
        doc.bezoekadres = mac.bezoekadres.volledig_adres
        doc.bezoekadres_correctie = mac.bezoekadres.correctie
        doc.centroid = get_centroid(mac.bezoekadres.geometrie, 'wgs84')

    if mac.postadres:
        doc.postadres = mac.postadres.volledig_adres

    return doc


def from_vestiging(ves: models.Vestiging):
    """
    Create a doc from a vestiging
    """

    doc = Inschrijving(_id=f'v{ves.id}')

    doc._display = str(ves)         # pylint: disable=protected-access
    doc.vestigingsnummer = ves.vestigingsnummer

    doc.doctype = 'ves'

    doc.hoofdvestiging = ves.hoofdvestiging

    doc.naam = ves.naam

    doc.handelsnamen.append(dict(naam=ves.naam))

    for h in ves.handelsnamen.all():
        doc.handelsnamen.append(dict(naam=h.handelsnaam))

    for act in ves.activiteiten.all():
        doc.sbi.append(dict(
            code=act.sbi_code, omschrijving=act.sbi_omschrijving))

    if ves.bezoekadres:
        doc.bezoekadres = ves.bezoekadres.volledig_adres
        doc.centroid = get_centroid(ves.bezoekadres.geometrie, 'wgs84')

        doc._kvk_display = re.split(    # pylint: disable=protected-access
            r"\d\d\d\d[a-z][a-z]", doc.bezoekadres)

    if ves.postadres:
        doc.postadres = ves.bezoekadres.volledig_adres

    return doc
