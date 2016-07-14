
from rest_framework import serializers

from datapunt import rest

from . import models


class MaatschappelijkeActiviteit(rest.HALSerializer):
    dataset = 'hr'

    _display = rest.DisplayField()

    class Meta:
        model = models.MaatschappelijkeActiviteit


#class MaatschappelijkeActiviteitDetail(serializers.ModelSerializer):
#    dataset = 'hr'
#
#    class Meta:
#        model = models.MaatschappelijkeActiviteit
#
