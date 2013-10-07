import os, sys
import tempfile
import shutil

import requests

from django.test.utils import override_settings

from instances.tests import InstanceTestCase

import speeches
from speeches.models import Speech, Speaker
from speeches.importers.import_json import ImportJson

@override_settings(POPIT_API_URL='http://sa-test.matthew.popit.dev.mysociety.org/api/v0.1/')
class ImportJsonTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs', 'committee')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_import(self):
        files = [
                # filename, speech count, resolved count, section title, section parent titles
                ('1.txt', 8, 0, "Agriculture, Forestry and Fisheries", ["Top Section", "Middle Section", "Bottom Section"]),
                ('2.txt', 6, 0, "Agriculture, Forestry and Fisheries", ["Top Section", "Middle Section", "Other Bottom Section"]),
                #('3.txt', 8, 0),
                #('4.txt', 5, 0),
                #('5.txt', 8, 0),
                #('6.txt', 9, 0),
                #('7.txt', 6, 0),
                #('8.txt', 6, 0),
                #('9.txt', 7, 0)
                ]

        sections = []

        for (f, exp_speeches, exp_resolved, exp_section_name, exp_section_parents) in files:
            document_path = os.path.join(self._in_fixtures, f)

            aj = ImportJson(instance=self.instance, category_field="title", commit=True)
            section = aj.import_document(document_path)

            sections.append(section)

            self.assertTrue(section is not None)

            # Check sections created as expected
            self.assertEqual(section.title, exp_section_name)
            parent_to_test = section.parent
            for exp_parent in reversed(exp_section_parents):
                self.assertEqual(parent_to_test.title, exp_parent)
                parent_to_test = parent_to_test.parent
            self.assertEqual(parent_to_test, None)

            speeches = section.speech_set.all()

            resolved = filter(lambda s: s.speaker.person != None, speeches)

            self.assertEquals( len(speeches), exp_speeches,
                   'Speeches %d == %d (%s)' %
                   (len(speeches), exp_speeches, f) )
            self.assertEquals( len(resolved), exp_resolved,
                   'Resolved %d == %d (%s)' %
                   (len(resolved), exp_resolved, f) )

        s0_grandparent = sections[0].parent.parent.parent
        s1_grandparent = sections[1].parent.parent.parent
        self.assertEquals( s0_grandparent.title, 'Top Section' )
        self.assertEquals( s1_grandparent.title, 'Top Section' )
        self.assertEquals( s0_grandparent.id, s1_grandparent.id )

