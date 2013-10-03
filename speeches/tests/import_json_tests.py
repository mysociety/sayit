import os, sys
import tempfile
import shutil

import requests

from instances.tests import InstanceTestCase

import speeches
from speeches.models import Speech, Speaker
from speeches.importers.import_json import ImportJson

class ImportJsonTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs', 'committee')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_import(self):
        files = [
                ('1.txt', 8, 0),
                #('2.txt', 6, 0),
                #('3.txt', 8, 0),
                #('4.txt', 5, 0),
                #('5.txt', 8, 0),
                #('6.txt', 9, 0),
                #('7.txt', 6, 0),
                #('8.txt', 6, 0),
                #('9.txt', 7, 0)
                ]
        
        for (f, exp_speeches, exp_resolved) in files:
            document_path = os.path.join(self._in_fixtures, f)

            aj = ImportJson(instance=self.instance, commit=True)
            section = aj.import_document(document_path)

            self.assertTrue(section is not None)

            speeches = section.speech_set.all()

            resolved = filter(lambda s: s.speaker.person != None, speeches)

            self.assertEquals( len(speeches), exp_speeches, 
                   'Speeches %d == %d (%s)' % 
                   (len(speeches), exp_speeches, f) )
            self.assertEquals( len(resolved), exp_resolved,
                   'Resolved %d == %d (%s)' % 
                   (len(resolved), exp_resolved, f) )
