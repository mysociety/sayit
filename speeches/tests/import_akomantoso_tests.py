import os, sys
import tempfile
import shutil

import requests

from django.test.utils import override_settings

from instances.tests import InstanceTestCase

import speeches
from speeches.models import Speech, Speaker
from speeches.importers.import_akomantoso import ImportAkomaNtoso

@override_settings(POPIT_API_URL='http://sa-test.matthew.popit.dev.mysociety.org/api/v0.1/')
class ImportAkomaNtosoTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_import(self):
        document_path = os.path.join(self._in_fixtures, 'NA200912.xml')

        an = ImportAkomaNtoso(instance=self.instance, commit=False)
        section = an.import_document(document_path)

        self.assertTrue(section is not None)

        speakers = Speaker.objects.all()
        resolved = filter(lambda s: s.person != None, speakers)
        THRESHOLD=48

        print >> sys.stderr, (
                "%d above threshold %d/%d?" 
                % (len(resolved), THRESHOLD, len(speakers)))

        self.assertTrue(
                len(resolved) >= THRESHOLD, 
                "%d above threshold %d/%d" 
                % (len(resolved), THRESHOLD, len(speakers)))
