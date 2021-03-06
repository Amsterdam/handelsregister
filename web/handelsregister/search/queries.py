
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

    def __init__(
            self,
            query: typing.Optional[dict],
            sort_fields: [str] = None,
            indexes: [str] = None,
            size: int = None,
            custom_sort_function: typing.Callable=None,
            aggs: dict = None):
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
        self.aggs = aggs

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

        if self.aggs:
            search.update_from_dict(self.aggs)

        search = search[0:size]

        return search


def inschrijvingen_query(
        analyzer: InputQAnalyzer, doctype=None, aggs=None) -> ElasticQueryWrapper:
    """ Create query/aggregation for vestiging search"""
    # vestigings nummer or handelsnaam
    vesid = kvknummer = analyzer.get_id()
    if len(vesid) < 5:
        kvknummer = vesid = ''

    handelsnaam = analyzer.get_handelsnaam()
    must = []

    if doctype:
        must = [Q('term', doctype=doctype)]

    sort_fields = ['_score']
    # sort_fields = ['_display']

    min_match = 1

    should = [
        Q(
            'multi_match',
            slop=12,  # match "stephan preeker" with "stephan jacob preeker"
            max_expansions=12,
            query=handelsnaam,
            type='phrase_prefix',
            fields=[
                "naam",
                "naam.ngram",
                "naam.raw",
            ]
        ),

        Q('prefix', naam=handelsnaam),

        # Nested handelsnamen
        Q(
            "nested",
            path="handelsnamen",
            score_mode="max",
            query=Q(
                'multi_match',
                slop=12,
                max_expansions=12,
                query=handelsnaam,
                type='phrase_prefix',
                fields=[
                    "handelsnamen.naam.ngram",
                    "handelsnamen.naam.raw",
                    "handelsnamen.naam"
                ]
            )
        )
    ]

    if vesid or kvknummer:
        should = [
            Q('prefix', vestigingsnummer__nozero=vesid),
            Q('prefix', vestigingsnummer=vesid),
            Q('prefix', kvk_nummer__nozero=kvknummer),
            Q('prefix', kvk_nummer=kvknummer)
        ]
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
        aggs=aggs
    )
