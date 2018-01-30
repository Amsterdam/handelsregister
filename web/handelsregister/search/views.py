# typeahead and Searchviews (Elasticsearch)
# and someone put geosearch in here ... :(

import json

import logging
from collections import OrderedDict
from collections import defaultdict
from urllib.parse import quote, urlparse

from django.conf import settings
from django.db import connection
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError
from elasticsearch_dsl import Search
from rest_framework import viewsets, metadata
from rest_framework.response import Response
from rest_framework.reverse import reverse

from search.queries import inschrijvingen_query
from search.geo_params import get_request_coord


from search.input_analyzer import InputQAnalyzer

log = logging.getLogger('search')

_details = {
    'ves': 'vestiging-detail',
    'mac': 'maatschappelijkeactiviteit-detail',
}


_type_mapping = {
    'ves': 'Vestigingen',
    'mac': 'Maatschappelijke activiteiten'
}


_autocomplete_group_order = [
    'Vestigingen',
    'Maatschappelijke activiteiten',
]


_autocomplete_group_sizes = {
    'Vestigingen': 10,
    'Maatschappelijke activiteiten': 5
}

_allowed_geoviews = [
    "bouw",
    "overheid_onderwijs_zorg",
    "productie_installatie_reparatie",
    "zakelijke_dienstverlening",
    "handel_vervoer_opslag",
    "landbouw",
    "persoonlijke_dienstverlening",
    "informatie_telecommunicatie",
    "cultuur_sport_recreatie",
    "financiele_dienstverlening_verhuur",
    "overige",
    "horeca",
]


def get_links(view_name, kwargs=None, request=None):
    result = OrderedDict([
        ('self', dict(
            href=reverse(view_name, kwargs=kwargs, request=request)
        ))
    ])

    return result


def _get_url(request, hit):
    """
    Given an elk hit determine the uri for each hit
    """

    doc_type, id = hit.doctype, hit.meta.id

    if doc_type == 'ves':
        return get_links(
            view_name=_details[doc_type],
            kwargs={'vestigingsnummer': hit.vestigingsnummer}, request=request)

    if doc_type == 'mac':
        return get_links(
            view_name=_details[doc_type],
            kwargs={'kvk_nummer': hit.kvk_nummer}, request=request)

    raise ValueError('doctype is unknown, can not build self url')


class QueryMetadata(metadata.SimpleMetadata):
    def determine_metadata(self, request, view):
        result = super().determine_metadata(request, view)
        result['parameters'] = {
            'q': {
                'type': 'string',
                'description': 'The query to search for',
                'required': True,
            },
        }
        return result


# =============================================
# Search view sets
# =============================================

class TypeaheadViewSet(viewsets.ViewSet):
    """
    Given a query parameter `q`, this function returns a
    subset of all matching maatschappelijke activiteit or
    vestigingen.

    *NOTE*

    We assume spelling errors and therefore it is possible
    to have unexpected results

    """
    metadata_class = QueryMetadata

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = Elasticsearch(settings.ELASTIC_SEARCH_HOSTS)

    def autocomplete_queries(self, query_string):
        """provide autocomplete suggestions"""

        analyzer = InputQAnalyzer(query_string)

        query_components = [
            inschrijvingen_query(analyzer)
            # vestiging_query(analyzer),
            # mac_query(analyzer)
        ]

        result_data = []

        # Ignoring cache in case debug is on
        ignore_cache = settings.TESTING

        # create elk queries
        for q in query_components:  # type: ElasticQueryWrapper

            search = q.to_elasticsearch_object(self.client)

            # get the result from elastic
            try:
                result = search.execute(ignore_cache=ignore_cache)
            except(TransportError):
                log.exception(
                    'FAILED ELK SEARCH: %s',
                    json.dumps(search.to_dict(), indent=2))
                continue
            # Get the datas!
            result_data.append(result)

        return result_data

    def _get_uri(self, request, hit):
        # Retrieves the uri part for an item
        url = _get_url(request, hit)['self']['href']
        uri = urlparse(url).path[1:]
        return uri

    def _group_elk_results(self, request, results):
        """
        Group the elk results in their pretty name groups
        """
        flat_results = (hit for r in results for hit in r)
        result_groups = defaultdict(list)

        for hit in flat_results:
            group = _type_mapping[hit.doctype]
            result_groups[group].append({
                '_display': hit._display,
                'uri': self._get_uri(request, hit)
            })

        return result_groups

    def _order_results(self, results, request):
        """
        Group the elastic search results and order these groups

        @Params
        result - the elastic search result object
        query_string - the query string used to search for. This is for exact
                       match recognition
        """

        # put the elk results in subtype groups
        result_groups = self._group_elk_results(request, results)

        ordered_results = []

        for group in _autocomplete_group_order:
            if group not in result_groups:
                continue

            size = _autocomplete_group_sizes[group]

            ordered_results.append({
                'label': group,
                'content': result_groups[group][:size]
            })

        return ordered_results

    def list(self, request):
        """
        Returns matching result options
        """

        if 'q' not in request.query_params:
            return Response([])

        query = request.query_params['q']
        if not query:
            return Response([])

        results = self.autocomplete_queries(query)
        response = self._order_results(results, request)

        return Response(response)


class SearchViewSet(viewsets.ViewSet):
    """
    Base class for ViewSets implementing search.
    """

    metadata_class = QueryMetadata
    page_size = 100
    url_name = 'search-list'
    page_limit = 10

    def search_query(self, client, analyzer: InputQAnalyzer) -> Search:
        """
        Construct the search query that is executed by this view set.
        """
        raise NotImplementedError

    def _set_followup_url(self, request, result, end,
                          response, query, page):
        """
        Add paging links for result set to response object
        """
        # make query url friendly again
        url_query = quote(query)
        # Finding link to self via reverse url search
        followup_url = reverse(self.url_name, request=request)

        self_url = "{}?q={}&page={}".format(
            followup_url, url_query, page)

        response['_links'] = OrderedDict([
            ('self', {'href': self_url}),
            ('next', {'href': None}),
            ('prev', {'href': None})
        ])

        # Finding and setting prev and next pages
        if end < result.hits.total:
            if end < (self.page_size * self.page_limit):
                # There should be a next
                response['_links']['next']['href'] = "{}?q={}&page={}".format(
                    followup_url, url_query, page + 1)
        if page == 2:
            response['_links']['prev']['href'] = "{}?q={}".format(
                followup_url, url_query)
        elif page > 2:
            response['_links']['prev']['href'] = "{}?q={}&page={}".format(
                followup_url, url_query, page - 1)

    def list(self, request, *args, **kwargs):
        """
        Create a response list
        """

        query = request.query_params.get('q')
        if not query:
            return Response([])

        page = 1
        if 'page' in request.query_params:
            # limit search results pageing in elastic is slow
            page = int(request.query_params['page'])
            if page > self.page_limit:
                page = self.page_limit

        start = ((page - 1) * self.page_size)
        end = (page * self.page_size)

        query = request.query_params['q']
        analyzer = InputQAnalyzer(query)

        client = Elasticsearch(
            settings.ELASTIC_SEARCH_HOSTS,
            raise_on_error=True
        )

        # get the result from elastic
        elk_query = self.search_query(client, analyzer)
        search = elk_query[start:end]

        if not search:
            log.debug('no elk query')
            return Response([])

        ignore_cache = settings.TESTING

        try:
            result = search.execute(ignore_cache=ignore_cache)
        except(TransportError):
            log.exception("Could not execute search query " + query)
            log.exception(json.dumps(search.to_dict(), indent=4))
            # Todo fix this
            # https://github.com/elastic/elasticsearch/issues/11340#issuecomment-105433439
            return Response([])

        if settings.DEBUG:
            log.info(json.dumps(search.to_dict(), indent=4))

        response = OrderedDict()

        self._set_followup_url(request, result, end, response, query, page)

        count = result.hits.total

        # log.exception(count)

        response['count'] = count

        response['results'] = [self.normalize_hit(h, request)
                               for h in result.hits]

        return Response(response)

    def get_url(self, request, hit):
        """
        """
        return _get_url(request, hit)

    def normalize_hit(self, hit, request):
        result = OrderedDict()
        result['_links'] = self.get_url(request, hit)
        result['type'] = hit.meta.doc_type
        result['dataset'] = hit.meta.index
        result.update(hit.to_dict())

        return result


class SearchVestigingViewSet(SearchViewSet):
    """
    Given a query parameter `q`, this function returns a subset of all
    vestiging objects that match the elastic search query.
    """

    url_name = 'search/vestiging-list'

    def search_query(self, client, analyzer: InputQAnalyzer) -> Search:
        """
        Execute search on Subject
        """
        search = inschrijvingen_query(analyzer, doctype='ves')\
            .to_elasticsearch_object(client)
        return search


class SearchMacViewSet(SearchViewSet):
    """
    Given a query parameter `q`, this function returns a subset of all
    maatschappelijke activiteit objects that match the elastic search query.
    """

    url_name = 'search/maatschappelijke_activiteit-list'

    def search_query(self, client, analyzer: InputQAnalyzer) -> Search:
        """
        Execute search on Subject
        """
        search = inschrijvingen_query(
            analyzer, doctype='mac').to_elasticsearch_object(client)
        return search


class SearchInschrijvingen(SearchViewSet):
    """
    Given a query parameter `q`, this function returns a subset of all
    maatschappelijke activiteit objects that match the elastic search query.
    """

    url_name = 'search/inschrijvingen-list'

    def search_query(self, client, analyzer: InputQAnalyzer) -> Search:
        """
        Execute search on Subject
        """
        search = inschrijvingen_query(analyzer).to_elasticsearch_object(client)
        return search


class GeoSearchViewSet(viewsets.ViewSet):
    """
    Given a query parameter `item`, `lat/lon` or `x/y combo` and
    optional `radius` parameter this function returns a subset of vestigingen.
    """
    url_name = 'geosearch'

    def list(self, request):
        if 'item' not in request.query_params:
            return Response([])

        hr_item = request.query_params['item']
        if hr_item not in _allowed_geoviews:
            return Response([])

        x, y = get_request_coord(request.query_params)
        if not x or not y:
            return Response([])

        radius = 30
        if 'radius' in request.query_params:
            radius = request.query_params['radius']

        features = self.run_query(hr_item, x, y, radius)

        return Response({"features": features})

    def run_query(self, view, x, y, radius):
        sql = f"""
SELECT DISTINCT
    naam as display,
    uri,
    'handelsregister/vestiging' as type,
    ST_Distance(
        geometrie, ST_GeomFromText(\'POINT(%s %s)\', 28992)) as distance
FROM geo_hr_vestiging_locaties_{view}
WHERE ST_DWithin(
    geometrie,
    ST_GeomFromText(\'POINT(%s %s)\', 28992), %s)
ORDER BY distance """

        results = []
        with connection.cursor() as cursor:
            cursor.execute(sql, (x, y, x, y, radius))
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                results.append({"properties": dict(zip(columns, row))})

        return results
