
from django.test import TestCase

from datasets.hr import models as hrmodels
from datasets.hr.tests import factories as hrfactories
from datasets.sbicodes import load_sbi_codes
from datasets.sbicodes import validate_codes

import logging

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
        Create and Test some ambiguous sbi codes
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

        cls.all_activities.extend(cls.bad_codes)

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

    def test_fix_voorloop_null(self):
        """
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


    def test_detection_invalid(self):
        """
        """
        invalid = validate_codes.find_invalid_activiteiten()
        log.debug(invalid)
        zero = validate_codes.find_0_sbicodes()
        log.debug(zero)
        not_placeable = validate_codes.not_placeable(invalid, zero)

        log.debug(not_placeable)
        self.assertEqual(len(not_placeable), 1)
        self.assertEqual(not_placeable[0][3], 'ik ben fout')

    def test
