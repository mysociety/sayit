# -*- coding: utf-8 -*-

import os

from django.core.management import call_command

from instances.tests import InstanceTestCase
from popit.models import ApiInstance
from popit_resolver.resolve import SetupEntities, EntityName

import speeches
from speeches.models import Speaker
from speeches.importers.import_akomantoso import ImportAkomaNtoso, title_case_heading

import logging
logging.disable(logging.WARNING)

popit_url='http://za-peoples-assembly.popit.mysociety.org/api/v0.1/'

class ImportAkomaNtosoTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')

        call_command('clear_index', interactive=False, verbosity=0)

        if not EntityName.objects.count():
            SetupEntities(popit_url).init_popit_data()
            call_command('update_index', verbosity=0)

    @classmethod
    def tearDownClass(cls):
        EntityName.objects.all().delete()
        ApiInstance.objects.all().delete()

    def test_import(self):
        document_path = os.path.join(self._in_fixtures, 'NA200912.xml')

        an = ImportAkomaNtoso(instance=self.instance, commit=True, popit_url=popit_url, title_case=True)
        section = an.import_document(document_path)

        self.assertTrue(section is not None)

        # Check that all the sections have correct looking titles
        for sub in section.children.all():
            self.assertFalse("Member'S" in sub.title)

        speakers = Speaker.objects.all()
        resolved = filter(lambda s: s.person != None, speakers)
        THRESHOLD=48

        logging.info(
                "%d above threshold %d/%d?"
                % (len(resolved), THRESHOLD, len(speakers)))

        self.assertTrue(
                len(resolved) >= THRESHOLD,
                "%d above threshold %d/%d"
                % (len(resolved), THRESHOLD, len(speakers)))


    def test_title_casing(self):
        tests = (
            # initial, expected
            ( "ALL CAPS", "All Caps"),
            ( "MEMBER'S Statement", "Member's Statement"),
            ( "member’s", "Member’s"),
        )

        for initial, expected in tests:
            self.assertEqual(title_case_heading(initial), expected)
