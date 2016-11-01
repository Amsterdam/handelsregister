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
from django.conf.urls import url, include
from django.conf import settings
from django.contrib import admin
from rest_framework import routers, views, reverse, renderers, schemas, response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework_swagger.renderers import OpenAPIRenderer
from rest_framework_swagger.renderers import SwaggerUIRenderer

from datasets.hr import views as hr_views
from search import views as search_views


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

        class Handelsregister(cls):
            pass

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


search.register(
    r'typeahead', search_views.TypeaheadViewSet, base_name='typeahead')

# Alias voor nummeraanduiding
search.register(
    r'vestiging',
    search_views.SearchVestigingViewSet, base_name='search/vestiging')
search.register(
    r'maatschappelijkeactiviteit',
    search_views.SearchMacViewSet,
    base_name='search/maatschappelijke_activiteit')

@api_view()
@renderer_classes(
    [SwaggerUIRenderer, OpenAPIRenderer, renderers.CoreJSONRenderer])
def schema_view(request):
    generator = schemas.SchemaGenerator(title='Handelsregister API')
    return response.Response(generator.get_schema(request=request))


urlpatterns = [
    url(r'^status/', include('health.urls', namespace='health')),
    url(r'^handelsregister/search/', include(search.urls)),
    url(r'^handelsregister/', include(hr_router.urls)),
    url('^handelsregister/docs/$', schema_view),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.extend([
        url(r'^__debug__/', include(debug_toolbar.urls)),
        url(r'^admin/', admin.site.urls),
        url(r'^explorer/', include('explorer.urls')),
    ])
