import os, sys
import tempfile
import shutil

import requests

from instances.tests import InstanceTestCase

import speeches
from speeches.models import Section
from speeches.importers.import_akomantoso import ImportAkomaNtoso

from django.core.management import call_command
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

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

    def test_bad_config(self):

        # is there equiv of perl's 'local' in Python?
        old_POPIT_API_URL = settings.POPIT_API_URL

        settings.POPIT_API_URL = None

        self.assertRaises(
                ImproperlyConfigured, 
                ImportAkomaNtoso, 
                instance=self.instance, 
                commit=False)

        settings.POPIT_API_URL = old_POPIT_API_URL
