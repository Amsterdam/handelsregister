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
from rest_framework import routers

from datasets.hr_stelselpedia import views as hr_views


class HandelsRegisterRouter(routers.DefaultRouter):
    """
    Handelsregister (HR)

    End point for different Handelsregister
    """
    def get_api_root_view(self):
        view = super().get_api_root_view()
        cls = view.cls

        class HandelsRegister(cls):
            pass

        HandelsRegister.__doc__ = self.__doc__
        return HandelsRegister.as_view()


hr_router = HandelsRegisterRouter()

hr_router.register(
    r'maatschappelijkeactiviteit',
    hr_views.MaatschappelijkeActiviteitViewSet
)


urlpatterns = [
    url(r'^status/', include('health.urls', namespace='health')),
    url(r'^handelsregister/', include(hr_router.urls))
]
