
# Python
import logging
import typing

from django.conf import settings
from elasticsearch_dsl import Q
from elasticsearch_dsl import Search

from search.input_analyzer import InputQAnalyzer

log = logging.getLogger('hr_Q')

HR = settings.ELASTIC_INDICES['HR']


"""
==================================================
 Individual search queries for external systems
--------------------------------------------------
 Each of these functions builds a query and,
 if needed an aggregation as well.
 They all return a dict with the Q and A keyes
==================================================
"""
# Python
# Packages
# from elasticsearch_dsl import Search, Q, A


class ElasticQueryWrapper(object):
    """
    Wrapper object for dynamically constructing elastic search queries.
    """

    def __init__(self,
                 query: typing.Optional[dict],
                 sort_fields: [str] = None,
                 indexes: [str] = None,
                 size: int = None,
                 custom_sort_function: typing.Callable = None
                 ):
        """
        :param query: an elastic search query
        :param sort_fields: an optional list of fields to use for
            server-side sorting
        :param indexes: an optional list of indexes to use

        :param size: an optional limit on size of the result set
        :param custom_sort_function: an optional function to use
            for client-side sorting
        """
        self.query = query
        self.sort_fields = sort_fields
        self.indexes = indexes
        self.size = size
        self.custom_sort_function = custom_sort_function

    def to_elasticsearch_object(self, client) -> Search:
        assert self.indexes

        search = (
            Search()
            .using(client)
            .index(*self.indexes)
            .query(self.query)
        )
        if self.sort_fields:
            search = search.sort(*self.sort_fields)

        size = 15  # default size
        if self.size:
            size = self.size

        search = search[0:size]

        return search


def vestiging_query(analyzer: InputQAnalyzer) -> ElasticQueryWrapper:
    """ Create query/aggregation for vestiging search"""
    # vestigings nummer or handelsnaam
    vesid = analyzer.get_id()
    handelsnaam = analyzer.get_handelsnaam()

    must = [Q('term', _type='vestiging')]

    # straatnaam huisnummer??

    # sort_fields = ['_display']

    sort_fields = ['_score']

    min_match = 1
    should = [
        # Naam
        {"prefix": {"naam": {
            "value": handelsnaam, "boost": 6.0}}},

        {"match": {"handelsnamen.naam": {
            "query": handelsnaam, "fuzziness": 2}}},

        {"match_phrase_prefix": {"naam": {
            "query": handelsnaam, "max_expansions": 5}}},

        # Nested handelsnamen
        Q(
            "nested",
            path="handelsnamen",
            score_mode="max",
            query=Q(
                "bool",
                should=[
                    {"term": {"handelsnamen.naam": {
                        "value": handelsnaam, "boost": 21.0}}},
                    {"prefix": {"handelsnamen.naam": {
                        "value": handelsnaam}}},
                    {"match": {"handelsnamen.naam": {
                        "query": handelsnaam, "fuzziness": 2}}},
                    {"match_phrase_prefix": {"handelsnamen.naam": {
                        "query": handelsnaam, "max_expansions": 5}}},
                    {"prefix": {"handelsnamen.naam.ngram": handelsnaam}},
                ])
        )
    ]

    if vesid:
        must.append(Q('prefix', vestigingsnummer=vesid))
        should = [Q('prefix', vestigingsnummer=vesid)]
        min_match = 1

    return ElasticQueryWrapper(
        query=Q(
            'bool',
            must=must,
            should=should,
            minimum_should_match=min_match),
        sort_fields=sort_fields,
        indexes=[HR],
        size=10,
    )


def mac_query(analyzer: InputQAnalyzer) -> ElasticQueryWrapper:
    """ Create query/aggregation for vestiging search"""
    # vestigings nummer or handelsnaam
    kvknummer = analyzer.get_id()

    handelsnaam = analyzer.get_handelsnaam()

    must = [Q('term', _type='maatschappelijke_activiteit')]

    min_match = 1
    should = [
        # naam
        {"prefix": {"naam": {
            "value": handelsnaam, "boost": 6.0}}},
        {"match": {"naam": {
            "query": handelsnaam, "boost": 6.0}}},

        {"match_phrase_prefix": {"naam": {
            "query": handelsnaam, "max_expansions": 5}}},

        # nested handelsnamen
        Q(
            "nested",
            path="handelsnamen",
            score_mode="max",
            query=Q(
                "bool",
                should=[
                    {"term": {"handelsnamen.naam": {
                        "value": handelsnaam, "boost": 21.0}}},
                    {"prefix": {"handelsnamen.naam": {
                        "value": handelsnaam}}},
                    {"match": {"handelsnamen.naam": {
                        "query": handelsnaam, "fuzziness": 2}}},
                    {"match_phrase_prefix": {"handelsnamen.naam": {
                        "query": handelsnaam, "max_expansions": 5}}},
                    {"prefix": {"handelsnamen.naam.ngram": handelsnaam}},
                ])
        )
    ]

    if kvknummer:
        must.append(Q('prefix', kvk_nummer=kvknummer))
        should = [Q('prefix', kvk_nummer=kvknummer)]
        min_match = 1

    # sort_fields = ['_display']
    # straatnaam huisnummer??
    sort_fields = ['_score']

    return ElasticQueryWrapper(
        query=Q(
            'bool',
            must=must,
            should=should,
            minimum_should_match=min_match),
        sort_fields=sort_fields,
        indexes=[HR],
        size=10,
    )