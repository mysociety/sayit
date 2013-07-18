import os
import tempfile
import shutil

import requests

from instances.tests import InstanceTestCase

import speeches
from speeches.models import Speech
from speeches.import_akomantoso import ImportAkomaNtoso

class ImportAkomaNtosoTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_import(self):
        document_path = os.path.join(self._in_fixtures, '502914_1.xml')

        an = ImportAkomaNtoso(instance=self.instance)
        section = an.import_xml(document_path)

        self.assertTrue(section is not None)
