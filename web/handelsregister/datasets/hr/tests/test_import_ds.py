# Packages
from django.core.management import call_command
from django.test import TestCase

from datasets.hr.models import DataSelectie
from datasets.hr.tests.factories import create_dataselectie_set


class DataselectieHrImportTest(TestCase):
    def test_datasel_import(self):

        create_dataselectie_set()

        call_command('run_import', '--dataselectie', verbosity=0)

        # this one is always there

        rows = DataSelectie.objects.all()
        self.assertGreater(len(rows), 0)

        fields_in_row = (
            'naam',
            'postadres',
            'bezoekadres',
            'activiteiten',
            'handelsnamen',
            'hoofdvestiging',
            'vestigingsnummer',
            'maatschappelijke_activiteit'
        )

        for row in rows:
            for f in fields_in_row:
                self.assertIn(f, row.api_json)

        row = rows[0]

        sub_models = (
            'maatschappelijke_activiteit',
            'bezoekadres',
            'postadres',
        )
        for sub_model in sub_models:
            self.assertIsInstance(row.api_json[sub_model], dict)

        self.assertIsInstance(row.api_json['activiteiten'], list)
        self.assertIsInstance(row.api_json['activiteiten'][0], dict)
        self.assertGreaterEqual(len(row.api_json), 1)
