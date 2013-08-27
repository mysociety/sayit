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
                ('1.txt', 10, 0),
                ('2.txt', 10, 1),
                ('3.txt', 10, 1),
                ('4.txt', 10, 1),
                ('5.txt', 10, 1),
                ('6.txt', 10, 1),
                ('7.txt', 10, 1),
                ('8.txt', 10, 1),
                ('9.txt', 10, 1)
                ]
        
        for (f, exp_speeches, exp_resolved) in files:
            document_path = os.path.join(self._in_fixtures, f)

            aj = ImportJson(instance=self.instance, commit=False)
            section = aj.import_document(document_path)

            self.assertTrue(section is not None)

            speeches = section.speech_set.all()
            resolved = filter(lambda s: s.speaker.person != None, speeches)

            self.assertEquals( len(speeches), exp_speeches, 
                   'Speeches %d == %d' % (len(speeches), exp_speeches) )
            self.assertEquals( len(resolved), exp_resolved,
                   'Resolved %d == %d' % (len(resolved), exp_resolved) )
