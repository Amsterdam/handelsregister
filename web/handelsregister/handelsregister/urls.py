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
from rest_framework import routers

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


hr_router = HandelsregisterRouter()

hr_router.register(
    r'maatschappelijkeactiviteit',
    hr_views.MaatschappelijkeActiviteitViewSet
)
hr_router.register(
    r'persoon',
    hr_views.PersoonViewSet
)
hr_router.register(
    r'vestiging', hr_views.VestigingViewSet
)
hr_router.register(
    r'functievervulling',
    hr_views.FunctievervullingViewSet
)


hr_router.register(
    r'typeahead', search_views.TypeaheadViewSet, base_name='typeahead')

# Alias voor nummeraanduiding
hr_router.register(
    r'search/vestiging',
    search_views.SearchVestigingViewSet, base_name='search/vestiging')
hr_router.register(
    r'search/maatschappelijkeactiviteit',
    search_views.SearchMacViewSet,
    base_name='search/maatschappelijkeactiviteit')


urlpatterns = [
    url(r'^status/', include('health.urls', namespace='health')),
    url(r'^handelsregister/', include(hr_router.urls)),
]

if settings.DEBUG:
    urlpatterns.extend([
        url('^admin/', admin.site.urls),
        url(r'^explorer/', include('explorer.urls')),
    ])
