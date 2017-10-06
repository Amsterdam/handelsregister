
import logging

from django.test import TestCase

from datasets.hr import models as hrmodels
from datasets.hr.tests import factories as hrfactories
from datasets.sbicodes import load_sbi_codes
from datasets.sbicodes import validate_codes


log = logging.getLogger(__name__)


class ValidateSBICodeTest(TestCase):
    """
    Test de voorloopnulllen fix
    Test laden van sbi codes
    """

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    @classmethod
    def setUpClass(cls):
        """
        Create and Test some ambiguous sbi codes, invalid code
        normal codes , too short codes and check if they are fixed.
        """
        super().setUpClass()
        # load sbi fixture tree(s)
        load_sbi_codes.build_all_sbi_code_trees()

        ambiguous_activiteiten = [(
            "1000000000016177190",
            "Vervaardigen van lederen kleding, tassen, portemonnaies, koffers, alsmede van dames- en herenbovenkleding van textiel alsmede winkel, markt- en groothandel hierin",   # noqa
            "1411",
            "Vervaardiging van kleding van leer",
            True
        ), (
            "1000000000042142540",
            "Melkveebedrijf",
            "1411",              # should be 01411
            "Houden van melkvee",
            True
        )]

        cls.all_activities = []

        cls.bad_codes = [
            hrmodels.Activiteit.objects.create(
                activiteitsomschrijving='foute dingen',
                sbi_code='000045',
                sbi_omschrijving='ik ben fout',
                hoofdactiviteit=True
            )
        ]

        cls.zeros_codes = [
            hrmodels.Activiteit.objects.create(
                id="000",
                activiteitsomschrijving='ik mis een nul',
                sbi_code='111',  # non ambiguous, just missing a zero
                sbi_omschrijving="Teelt van granen, peulvruchten en oliehoudende zaden",  # noqa
                hoofdactiviteit=True
            )
        ]

        cls.too_short = [
            hrmodels.Activiteit.objects.create(
                id="024",
                activiteitsomschrijving='nul too short',
                sbi_code='024',  # missing a 1
                sbi_omschrijving="Dienstverlening voor de bosbouw",  # noqa
                hoofdactiviteit=True
            ),
            hrmodels.Activiteit.objects.create(
                id="8520",
                activiteitsomschrijving='missing 1 2 3',
                sbi_code='8520',  # missing 2
                sbi_omschrijving="Primair en speciaal onderwijs",  # noqa
                hoofdactiviteit=True
            )

        ]

        cls.default_ones = [
            # 'ongeclassificeerd' en 'geen bedrijfsactiviteiten'
            hrmodels.Activiteit.objects.create(
                id="01",
                activiteitsomschrijving='2 nuls too short',
                sbi_code='1',  # missing 2 zero's
                sbi_omschrijving="ongeclassificeerd",  # noqa
                hoofdactiviteit=True
            ),
            hrmodels.Activiteit.objects.create(
                id="02",
                activiteitsomschrijving='2 nulls missing 1 2 3',
                sbi_code='2',  # missing 2 zero's
                sbi_omschrijving="geen bedrijfsactiviteiten",  # noqa
                hoofdactiviteit=True
            )
        ]

        cls.all_activities.extend(cls.bad_codes)
        cls.all_activities.extend(cls.zeros_codes)
        cls.all_activities.extend(cls.too_short)
        cls.all_activities.extend(cls.default_ones)

        def save_activiteit(act):
            t_act = hrmodels.Activiteit.objects.create(
                id=act[0],
                activiteitsomschrijving=act[1],
                sbi_code=act[2],
                sbi_omschrijving=act[3],
                hoofdactiviteit=True,
            )
            t_act.save()

            cls.all_activities.append(t_act)

        for act in ambiguous_activiteiten:
            save_activiteit(act)

        # Create a vestiging for each activiteit
        for activiteit in cls.all_activities:
            hrfactories.VestigingFactory.create(
                naam=f'test_{activiteit.sbi_code}',
                activiteiten=[activiteit]
            )

    def test_fix_ambiguous_zero(self):
        """
        Fix cases which are ambiguous
        """
        ambiguous = validate_codes.find_ambiguous_sbicodes()
        self.assertEqual(len(ambiguous), 2)
        validate_codes.fix_ambiguous(ambiguous)
        ambiguous = validate_codes.find_ambiguous_sbicodes()
        self.assertEqual(len(ambiguous), 1)

        a = hrmodels.Activiteit.objects.get(sbi_code='01411')
        v = hrmodels.Vestiging.objects.filter(activiteiten__in=[a.id])
        self.assertEqual(len(v), 1)
        self.assertEqual(a.activiteitsomschrijving, 'Melkveebedrijf')

    def test_fix_missing_zero(self):
        """
        Some codes miss zero's and are valid with zero's
        """
        # invalid = find_invalid_activiteiten()
        ambiguous = validate_codes.find_ambiguous_sbicodes()
        zero = validate_codes.find_0_sbicodes()
        validate_codes.fix_missing_zero(ambiguous, zero)
        a = hrmodels.Activiteit.objects.get(id='000')
        self.assertEqual(a.sbi_code, '0111')

    def test_detection_invalid(self):
        """
        Some codes are invalid, test that we find them
        """
        invalid = validate_codes.find_invalid_activiteiten()
        log.debug(invalid)
        # find all codes that have a valid 0 couterpart
        zero = validate_codes.find_0_sbicodes()
        log.debug(zero)

        # find all codes that are invalid and do not have
        # a zero counterparkt
        not_placeable = validate_codes.not_placeable(invalid, zero)

        log.debug(not_placeable)
        self.assertEqual(len(not_placeable), 1)
        self.assertEqual(not_placeable[0][3], 'ik ben fout')

    def test_add_missing_activities(self):
        """
        if code is for company is too short to be an official
        sbi_code, expand the activities of vestiging with
        extra fields
        """

        ves = hrmodels.Vestiging.objects.get(naam='test_8520')
        self.assertEqual(ves.activiteiten.count(), 1)
        # find too short codes / not matched codes
        short_sbi_codes = validate_codes.find_expanded_sbi_for_too_short_sbi()
        log.debug(short_sbi_codes)
        self.assertEqual(len(short_sbi_codes), 3)
        validate_codes.fix_too_short(short_sbi_codes)

        # now missing activities should be added
        ves = hrmodels.Vestiging.objects.get(naam='test_8520')
        self.assertEqual(ves.activiteiten.count(), 4)

        # add new activities for vestigingen

        # validate they are created

    def test_correct_bouw_productie(self):
        """
        2 categories have more then 100 sbi codes
        and are not properly downloaded...
        """
        missing_qa = validate_codes.find_missing_qa()
        self.assertTrue(len(missing_qa) > 0)
        validate_codes.fix_manual_missing_qa(missing_qa)
        missing_qa = validate_codes.find_missing_qa()
        self.assertEqual(len(missing_qa), 0)

    def test_defaultcode_correction(self):
        """
        2 categories
        """
        ves1 = hrmodels.Vestiging.objects.get(naam='test_1')
        ves2 = hrmodels.Vestiging.objects.get(naam='test_2')
        validate_codes.fix_missing_zeros_default()

        self.assertEqual(ves1.activiteiten.count(), 1)
        self.assertEqual(ves2.activiteiten.count(), 1)
        self.assertEqual(ves1.activiteiten.all()[0].sbi_code, '0001')
        self.assertEqual(ves2.activiteiten.all()[0].sbi_code, '0002')
