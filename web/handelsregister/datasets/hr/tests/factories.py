import factory
from factory import fuzzy

from .. import models


class MaatschappelijkeActiviteitFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.MaatschappelijkeActiviteit

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)
    kvk_nummer = fuzzy.FuzzyInteger(low=1, high=99999999)


class PersoonFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Persoon

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)
    faillissement = False


class VestigingFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Vestiging

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)
    vestigingsnummer = fuzzy.FuzzyInteger(low=1, high=9999999)
    hoofdvestiging = fuzzy.FuzzyChoice(choices=[True, False])
    maatschappelijke_activiteit = factory.SubFactory(
        MaatschappelijkeActiviteitFactory)

    @factory.post_generation
    def activiteiten(self, create, activiteiten=None, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if activiteiten:
            # A list of groups were passed in, use them
            for a in activiteiten:
                self.activiteiten.add(a)


class LocatieFactory(factory.DjangoModelFactory):

    class Meta:
        model = models.Locatie

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)

    afgeschermd = fuzzy.FuzzyChoice(choices=[True, False])

    bag_numid = fuzzy.FuzzyChoice(choices=[1, 2])  # 'put_in_fixture_id'
    bag_vbid = fuzzy.FuzzyChoice(choices=[3, 4])  # 'put_in_fixture_id'


class Activiteit(factory.DjangoModelFactory):
    class Meta:
        model = models.Activiteit

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)

    sbi_code = fuzzy.FuzzyInteger(low=10000, high=10099)

    hoofdactiviteit = fuzzy.FuzzyChoice(choices=[True, False])


class FunctievervullingFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Functievervulling

    id = fuzzy.FuzzyInteger(low=100000000000000000, high=100000000000000099)
