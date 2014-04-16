from speeches.tests import InstanceTestCase
from speeches.models import Speaker, Speech, Section
from popit.models import Person, ApiInstance

import sys

class SpeakerTests(InstanceTestCase):
    """Tests for the speaker functionality"""

    def test_speaker_page_lists_speeches(self):
        # Add a speaker

        api_url = 'http://popit.mysociety.org/api/v1/'
        ai = ApiInstance.objects.create(url=api_url)

        popit_person = Person.objects.create(name='Steve', summary='A froody dude', image='http://example.com/image.jpg', api_instance=ai)
        speaker = Speaker.objects.create(name='Steve', instance=self.instance, person=popit_person)
        
        # Call the speaker's page
        resp = self.client.get('/speaker/%s' % speaker.slug)

        self.assertSequenceEqual("Steve", resp.context['speaker'].person.name)
        self.assertSequenceEqual("A froody dude", resp.context['speaker'].person.summary)
        self.assertSequenceEqual("http://example.com/image.jpg", resp.context['speaker'].person.image)

        # Assert no speeches
        self.assertSequenceEqual([], resp.context['speech_list'])
        self.assertSequenceEqual([], resp.context['page_obj'])

        # Add a speech
        speech = Speech.objects.create(text="A test speech", speaker=speaker, instance=self.instance)

        # Call the speaker's page again
        resp = self.client.get('/speaker/%s' % speaker.slug)

        self.assertSequenceEqual([speech], resp.context['speech_list'])
        self.assertSequenceEqual([speech], resp.context['page_obj'])

    def test_speaker_page_has_button_to_add_speech(self):
        # Add a speaker
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)
        
        # Call the speaker's page
        resp = self.client.get('/speaker/%s' % speaker.slug)

        self.assertContains(resp, '<a href="/speech/add?speaker=%d">Add a new speech</a>' % speaker.id, html=True)

    def test_speaker_popit_headshots_in_speeches_section(self):
        # Test that headshots vs default image work OK

        api_url = 'http://popit.mysociety.org/api/v1/'
        ai = ApiInstance.objects.create(url=api_url)

        person1 = Person.objects.create(name='Marilyn', summary='movie star', image='http://example.com/image.jpg', api_instance=ai)
        speaker1 = Speaker.objects.create(name='Marilyn', person=person1, instance=self.instance)
        speaker2 = Speaker.objects.create(name='Salinger', instance=self.instance)

        section = Section.objects.create(title='Test Section', instance=self.instance)

        speech1 = Speech.objects.create( text="A girl doesn't need anyone that doesn't need her.", speaker=speaker1, section=section, instance=self.instance, public=True )

        speech2 = Speech.objects.create( text="I'm sick of not having the courage to be an absolute nobody.", speaker=speaker2, section=section, instance=self.instance, public=True )

        resp = self.client.get('/sections/' + str(section.id))

        self.assertRegexpMatches(resp.content, r'(?s)<img src="\s*http://example.com/image.jpg\s*".*?<a href="/speaker/%s">\s*' % (speaker1.slug))

        self.assertRegexpMatches(resp.content, r'(?s)<img src="\s*/static/speeches/i/a.\w+.png\s*".*?<a href="/speaker/%s">\s*' % (speaker2.slug))
