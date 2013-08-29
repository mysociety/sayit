import os, sys
import tempfile
import shutil

import requests

from instances.tests import InstanceTestCase

import speeches
from speeches.models import Section
from django.core.management import call_command

class ImportCommandTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')

    @classmethod
    def tearDownClass(cls):
        pass

    def test_management_command(self):
        document_path = os.path.join(self._in_fixtures, 'NA200912.xml')

        pre_count = Section.objects.filter(  parent=None ).count()

        call_command('load_akomantoso', 
            file = document_path,
            commit = True,
            instance = self.instance.label,
            )

        post_count = Section.objects.filter(  parent=None ).count()

        print >> sys.stderr, '%d - %d\n' % (pre_count, post_count)

        self.assertEquals( pre_count + 1, post_count, 'New section was created' )

