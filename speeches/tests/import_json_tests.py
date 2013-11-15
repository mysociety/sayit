import os
from datetime import date

from django.core.management import call_command

from instances.tests import InstanceTestCase
from popit.models import ApiInstance
from popit_resolver.resolve import SetupEntities, ResolvePopitName, EntityName

import speeches
from speeches.importers.import_json import ImportJson

POPIT_API_URL='http://za-peoples-assembly.popit.mysociety.org/api/v0.1/'

class ImportJsonTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs', 'committee')

        call_command('clear_index', interactive=False, verbosity=0)

        if not EntityName.objects.count():
            SetupEntities(POPIT_API_URL).init_popit_data()
            call_command('update_index', verbosity=0)

    @classmethod
    def tearDownClass(cls):
        EntityName.objects.all().delete()
        ApiInstance.objects.all().delete()

    def test_resolve(self):
        resolver = ResolvePopitName(date=date(2013, 06, 21))
        person = resolver.get_person('Mrs A Steyn')
        self.assertTrue( person )

    def test_import(self):
        expecteds = [
            {
                "filename": "1.json",
                "speech_count": 8,
                "resolved_count": 7,
                "section_title": "Agriculture, Forestry and Fisheries",
                "section_parent_titles": ["Top Section", "Middle Section", "Bottom Section"],
                "is_public": True,
                "start_date": date(2013, 06, 21),
                "start_time": None,
                "end_date": date(2013, 06, 21),
                "end_time": None,
            },
            {
                "filename": "2.json",
                "speech_count": 6,
                "resolved_count": 6,
                "section_title": "Agriculture, Forestry and Fisheries",
                "section_parent_titles": ["Top Section", "Middle Section", "Other Bottom Section"],
                "is_public": False,
                "start_date": date(2013, 06, 19),
                "start_time": None,
                "end_date": date(2013, 06, 19),
                "end_time": None,
            },
            # {"filename": '3.json', "speech_count": 8, "resolved_count": 0},
            # {"filename": '4.json', "speech_count": 5, "resolved_count": 0},
            # {"filename": '5.json', "speech_count": 8, "resolved_count": 0},
            # {"filename": '6.json', "speech_count": 9, "resolved_count": 0},
            # {"filename": '7.json', "speech_count": 6, "resolved_count": 0},
            # {"filename": '8.json', "speech_count": 6, "resolved_count": 0},
            # {"filename": '9.json', "speech_count": 7, "resolved_count": 0}
        ]

        sections = []

        for expected in expecteds:
            document_path = os.path.join(self._in_fixtures, expected["filename"])

            aj = ImportJson(instance=self.instance, category_field="title", commit=True)
            section = aj.import_document(document_path)

            sections.append(section)

            self.assertTrue(section is not None)

            # Check sections created as expected
            self.assertEqual(section.title, expected["section_title"])
            parent_to_test = section.parent
            for exp_parent in reversed(expected["section_parent_titles"]):
                self.assertEqual(parent_to_test.title, exp_parent)
                parent_to_test = parent_to_test.parent
            self.assertEqual(parent_to_test, None)

            speeches = section.speech_set.all()

            # Check that all speeches have the correct privacy setting
            for speech in speeches:
                self.assertEqual(speech.public, expected["is_public"])

                # check that all speeches have the expected date
                self.assertEqual(speech.start_date, expected['start_date'])
                self.assertEqual(speech.start_time, expected['start_time'])
                self.assertEqual(speech.end_date,   expected['end_date'])
                self.assertEqual(speech.end_time,   expected['end_time'])

            resolved = filter(lambda s: s.speaker.person != None, speeches)

            self.assertEquals( len(speeches), expected["speech_count"],
                   'Speeches %d == %d (%s)' %
                   (len(speeches), expected["speech_count"], expected["filename"]) )
            self.assertEquals( len(resolved), expected["resolved_count"],
                   'Resolved %d == %d (%s)' %
                   (len(resolved), expected["resolved_count"], expected["filename"]) )

        s0 = sections[0]
        s1 = sections[1]

        self.assertEquals( s0.title, s1.title )
        self.assertNotEquals( s0.id, s1.id )

        s0_grandparent = s0.parent.parent.parent
        s1_grandparent = s1.parent.parent.parent
        self.assertEquals( s0_grandparent.title, 'Top Section' )
        self.assertEquals( s1_grandparent.title, 'Top Section' )
        self.assertEquals( s0_grandparent.id, s1_grandparent.id )

