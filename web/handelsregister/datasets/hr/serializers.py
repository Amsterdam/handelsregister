
from rest_framework import serializers

# from datapunt import rest

from . import models


class MaatschappelijkeActiviteit(serializers.ModelSerializer):

    class Meta:
        model = models.MaatschappelijkeActiviteit



