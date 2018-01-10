"""handelsregister URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

import collections
import operator

from django.conf import settings
from django.conf.urls import url, include
from django.views.generic.base import TemplateView
from rest_framework import routers, renderers, schemas, response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework_swagger.renderers import OpenAPIRenderer
from rest_framework_swagger.renderers import SwaggerUIRenderer

from datasets.hr import views as hr_views
from search import views as search_views


from rest_framework.reverse import reverse
from rest_framework.response import Response


class HandelsregisterRouter(routers.DefaultRouter):
    """
    Handelsregister (HR)

    Endpoint for handelsregister. De Basisregistratie Handelsregister is een
    administratie van (rechts)personen, maatschappelijke nevenactiviteiten
    waaronder ondernemingen en vestigingen, en legt vast hoe deze zich
    onderling verhouden.
    """

    def get_api_root_view(self, **kwargs):
        view = super().get_api_root_view(**kwargs)
        cls = view.cls

        api_root_dict = {}
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)

        class Handelsregister(cls):
            _ignore_model_permissions = True

            def get(self, request, format=None):
                ret = {}

                for key, url_name in api_root_dict.items():
                    ret[key] = reverse(
                        url_name, request=request, format=format)

                sorted_endpoints = sorted(
                        ret.items(), key=operator.itemgetter(0))

                sorted_ret = collections.OrderedDict(sorted_endpoints)

                return Response(sorted_ret)

        Handelsregister.__doc__ = self.__doc__
        return Handelsregister.as_view()


class SearchRouter(routers.DefaultRouter):
    """
    Search

    End point for different search uris, offering data not directly reflected
    in the models
    """

    def get_api_root_view(self, **kwargs):
        view = super().get_api_root_view(**kwargs)
        cls = view.cls

        class Search(cls):
            pass

        Search.__doc__ = self.__doc__
        return Search.as_view()


hr_router = HandelsregisterRouter()

hr_router.register(r'maatschappelijkeactiviteit',
                   hr_views.MaatschappelijkeActiviteitViewSet)
hr_router.register(r'persoon',
                   hr_views.PersoonViewSet)
hr_router.register(r'vestiging',
                   hr_views.VestigingViewSet)
hr_router.register(r'functievervulling',
                   hr_views.FunctievervullingViewSet)

search = SearchRouter()

typeahead = SearchRouter()

geosearch = SearchRouter()

typeahead.register(
    r'', search_views.TypeaheadViewSet, base_name='typeahead')

# Alias voor nummeraanduiding
search.register(
    r'vestiging',
    search_views.SearchVestigingViewSet, base_name='search/vestiging')
search.register(
    r'maatschappelijkeactiviteit',
    search_views.SearchMacViewSet,
    base_name='search/maatschappelijke_activiteit')

geosearch.register(
    r'', search_views.GeoSearchViewSet, base_name='geosearch')

grouped_url_patterns = {
    'base_patterns': [
        url(r'^status/', include('health.urls')),
    ],
    'hr_patterns': [
        url(r'^handelsregister/', include(hr_router.urls)),
        url(r'^handelsregister/search/', include(search.urls)),
    ],
    'typeahead_patterns': [
        url(r'^handelsregister/typeahead/', include(typeahead.urls)),
    ],
    'geosearch-patterns': [
        url(r'^handelsregister/geosearch/', include(geosearch.urls)),
    ]
}


@api_view()
@renderer_classes(
    [OpenAPIRenderer, renderers.CoreJSONRenderer])
def hr_schema_view(request):
    generator = schemas.SchemaGenerator(title='Handelsregister API')
    return response.Response(generator.get_schema(request=request))


class OpenAPIView(TemplateView):

    template_name = "openapi.yml"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        host = self.request.META['HTTP_HOST']
        if host.startswith('localhost'):
            context['apihost'] = 'http://' + host
            context['oauth2host'] = 'http://localhost:8686'
        else:
            context['apihost'] = 'https://' + host
            context['oauth2host'] = 'https://' + host

urlpatterns = [
                  url('^handelsregister/docs/openapi.yml', OpenAPIView.as_view()),
                  url('^handelsregister/docs/api-docs/$', hr_schema_view),
              ] + [url for pattern_list in grouped_url_patterns.values()
                   for url in pattern_list]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns.extend([
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ])
