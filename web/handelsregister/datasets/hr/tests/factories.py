import factory
from factory import fuzzy

from .. import models


class MaatschappelijkeActiviteitFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.MaatschappelijkeActiviteit

    macid = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)


class PersoonFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Persoon

    prsid = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)


class VestigingFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Vestiging

    vesid = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)


class FunctievervullingFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Functievervulling

    ashid = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)
