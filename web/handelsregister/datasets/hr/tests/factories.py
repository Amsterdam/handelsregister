import factory
from factory import fuzzy

from .. import models


class MaatschappelijkeActiviteitFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.MaatschappelijkeActiviteit

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)


class PersoonFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Persoon

    prsid = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)



class VestigingFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Vestiging

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)
    hoofdvestiging = fuzzy.FuzzyChoice(choices=[True, False])
    maatschappelijke_activiteit = factory.SubFactory(MaatschappelijkeActiviteitFactory)


class FunctievervullingFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Functievervulling

    fvvid = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)
