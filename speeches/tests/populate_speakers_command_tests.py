from mock import patch, Mock

from django.core import management
from django.conf import settings
from django.test.utils import override_settings

from popit.models import ApiInstance, Person
from speeches.tests import InstanceTestCase
from speeches.models import Speaker

class PopulateSpeakersCommandTests(InstanceTestCase):

    popit_url = 'http://popit.mysociety.org/api/v1/'

    def test_populates_empty_db(self):
        api_url = self.popit_url
        ai = ApiInstance.objects.create(url=api_url)

        # Canned data to simulate a response from popit-api
        people = [
            {
                'id': 'abcde',
                'name': 'Test 1',
                'popit_url': 'abcde',
            },
            {
                'id': 'fghij',
                'name': 'Test 2',
                'popit_url': 'fghij',
            }
        ]
        # Mock out popit and then call our command
        m = Mock()
        m._store = { 'base_url': api_url + 'persons' }
        m.get.return_value = { 'result': people }
        with patch('popit.models.ApiInstance.api_client', return_value=m) as patched_popit:
            management.call_command('popit_retrieve_all')

        db_people = Person.objects.all()
        self.assertEqual(len(db_people), 2)
        self.assertEqual(db_people[0].popit_url, api_url + 'persons/abcde')
        self.assertEqual(db_people[0].name, 'Test 1')
        self.assertEqual(db_people[0].api_instance, ai)
        self.assertEqual(db_people[1].popit_url, api_url + 'persons/fghij')
        self.assertEqual(db_people[1].name, 'Test 2')
        self.assertEqual(db_people[1].api_instance, ai)

    def test_updates_existing_records(self):
        api_url = self.popit_url
        ai = ApiInstance.objects.create(url=api_url)

        # Add a record into the db first
        existing_person = Person.objects.create(popit_url=api_url + 'persons/abcde', name='test 1', api_instance=ai)
        existing_speaker = Speaker.objects.create(person=existing_person, name='Test Override', instance=self.instance)

        # Canned data to simulate a response from popit
        changed_people = [
            {
                'id': 'abcde',
                'name': 'Test 3', # Note changed name
                'popit_url': api_url + 'persons/abcde',
            },
            {
                'id': 'fghij',
                'name': 'Test 2',
                'popit_url': api_url + 'persons/fghij',
            }
        ]
        # Mock out popit and then call our command
        m = Mock()
        m._store = { 'base_url': api_url + 'persons' }
        m.get.return_value = { 'result': changed_people }
        with patch('popit.models.ApiInstance.api_client', return_value=m) as patched_popit:
            management.call_command('popit_retrieve_all')

        db_people = Person.objects.all()
        self.assertEqual(len(db_people), 2)
        self.assertEqual(db_people[0].popit_url, api_url + 'persons/abcde')
        self.assertEqual(db_people[0].name, 'Test 3')
        self.assertEqual(db_people[0].api_instance, ai)
        self.assertEqual(db_people[1].popit_url, api_url + 'persons/fghij')
        self.assertEqual(db_people[1].name, 'Test 2')
        self.assertEqual(db_people[1].api_instance, ai)

        self.assertEqual(existing_speaker.name, 'Test Override')
        self.assertEqual(existing_speaker.person, db_people[0])
