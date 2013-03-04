from mock import patch, Mock

from popit import PopIt

from django.core import management

from instances.tests import InstanceTestCase

import speeches
from speeches.models import Speaker

class PopulateSpeakersCommandTests(InstanceTestCase):

    def test_populates_empty_db(self):
        # Canned data to simulate a response from popit
        people = [
            {
                '_id': 'abcde',
                'name': 'Test 1',
                'meta': {
                    'api_url': 'http://popit.mysociety.org/api/v1/person/abcde',
                },
            },
            {
                '_id': 'fghij',
                'name': 'Test 2',
                'meta': {
                    'api_url': 'http://popit.mysociety.org/api/v1/person/fghij',
                },
            }
        ]
        # Mock out popit and then call our command
        popit_config = { 'person': Mock(), 'person.get.return_value': {'results': people} }
        with patch('speeches.management.commands.populatespeakers.PopIt', spec=PopIt, **popit_config) as patched_popit:
            management.call_command('populatespeakers', instance='testing')

        db_people = Speaker.objects.all()
        self.assertTrue(len(db_people) == 2)
        self.assertTrue(db_people[0].popit_url == 'http://popit.mysociety.org/api/v1/person/abcde')
        self.assertTrue(db_people[0].name == 'Test 1')
        self.assertTrue(db_people[1].popit_url == 'http://popit.mysociety.org/api/v1/person/fghij')
        self.assertTrue(db_people[1].name == 'Test 2')

    def test_updates_existing_records(self):
        # Add a record into the db first
        existing_person = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/abcde', name='test 1', instance=self.instance)

        # Canned data to simulate a response from popit
        changed_people = [
            {
                '_id': 'abcde',
                'name': 'Test 3', # Note changed name
                'meta': {
                    'api_url': 'http://popit.mysociety.org/api/v1/person/abcde',
                },
            },
            {
                '_id': 'fghij',
                'name': 'Test 2',
                'meta': {
                    'api_url': 'http://popit.mysociety.org/api/v1/person/fghij',
                },
            }
        ]
        # Mock out popit and then call our command
        popit_config = { 'person': Mock(), 'person.get.return_value': {'results': changed_people} }
        with patch('speeches.management.commands.populatespeakers.PopIt', spec=PopIt, **popit_config) as new_patched_popit:
            management.call_command('populatespeakers', instance='testing')

        db_people = Speaker.objects.all()
        self.assertTrue(len(db_people) == 2)
        self.assertTrue(db_people[0].popit_url == 'http://popit.mysociety.org/api/v1/person/abcde')
        self.assertTrue(db_people[0].name == 'Test 3')
        self.assertTrue(db_people[1].popit_url == 'http://popit.mysociety.org/api/v1/person/fghij')
        self.assertTrue(db_people[1].name == 'Test 2')
