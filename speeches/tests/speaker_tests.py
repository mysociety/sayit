from instances.tests import InstanceTestCase

from speeches.models import Speaker, Speech
from popit.models import Person, ApiInstance

class SpeakerTests(InstanceTestCase):
    """Tests for the speaker functionality"""

    def test_speaker_page_lists_speeches(self):
        # Add a speaker

        api_url = 'http://popit.mysociety.org/api/v1/'
        ai = ApiInstance.objects.create(url=api_url)

        popit_person = Person.objects.create(name='Steve', summary='A froody dude', image='http://example.com/image.jpg', api_instance=ai)
        speaker = Speaker.objects.create(name='Steve', instance=self.instance, person=popit_person)
        
        # Call the speaker's page
        resp = self.client.get('/speaker/1')

        self.assertSequenceEqual("Steve", resp.context['speaker'].person.name)
        self.assertSequenceEqual("A froody dude", resp.context['speaker'].person.summary)
        self.assertSequenceEqual("http://example.com/image.jpg", resp.context['speaker'].person.image)

        # Assert no speeches
        self.assertSequenceEqual([], resp.context['speech_list'])

        # Add a speech
        speech = Speech.objects.create(text="A test speech", speaker=speaker, instance=self.instance)

        # Call the speaker's page again
        resp = self.client.get('/speaker/1')

        self.assertSequenceEqual([speech], resp.context['speech_list'])

    def test_speaker_page_has_button_to_add_speech(self):
        # Add a speaker
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)
        
        # Call the speaker's page
        resp = self.client.get('/speaker/1')

        self.assertContains(resp, '<a href="/speech/add?speaker=1">Add a new speech</a>', html=True)
