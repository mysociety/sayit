import sys
import re
from datetime import date
from mock import patch, Mock

import django
from django.test.utils import override_settings
from django.utils.six import assertRegex
from django.utils.six.moves import builtins
from easy_thumbnails.templatetags import thumbnail

from speeches.tests import InstanceTestCase
from speeches.models import Speaker, Speech, Section
from speeches import models

m = Mock()
m.return_value = ('speeches/fixtures/test_inputs/Ferdinand_Magellan.jpg', None)

@override_settings(MEDIA_URL='/uploads/')
@patch.object(models, 'urlretrieve', m)
class SpeakerTests(InstanceTestCase):
    """Tests for the speaker functionality"""

    def tearDown(self):
        if hasattr(self, 'speaker'):
            self.speaker.image_cache.delete(save=False)

    def test_speaker_page_lists_speeches(self):
        # Add a speaker
        self.speaker = speaker = Speaker.objects.create(
            name='Steve', instance=self.instance,
            summary='A froody dude',
            image='http://example.com/image.jpg')

        # Call the speaker's page
        resp = self.client.get('/speaker/%s' % speaker.slug)

        self.assertSequenceEqual("Steve", resp.context['speaker'].name)
        self.assertSequenceEqual("A froody dude", resp.context['speaker'].summary)
        self.assertSequenceEqual("http://example.com/image.jpg", resp.context['speaker'].image)

        # Assert no speeches
        self.assertSequenceEqual([], resp.context['speech_list'])
        self.assertSequenceEqual([], resp.context['page_obj'])

        # Add a speech
        speech = Speech.objects.create(
            text="A test speech",
            speaker=speaker,
            instance=self.instance,
            start_date=date(2014, 9, 17),
            )

        # Call the speaker's page again
        resp = self.client.get('/speaker/%s' % speaker.slug)

        self.assertSequenceEqual([speech], resp.context['speech_list'])
        self.assertSequenceEqual([speech], resp.context['page_obj'])

        # Add another speech on the same date and check that both dates are displayed
        speech = Speech.objects.create(
            text="Another speech",
            speaker=speaker,
            instance=self.instance,
            start_date=date(2014, 9, 17),
            )

        # Check that a search which returns more than one speech on the same
        # date displays a date for each.
        resp = self.client.get('/speaker/%s' % speaker.slug)
        self.assertEqual(len(re.findall(r'<span class="breadcrumbs__date">\s*17 Sep 2014\s*</span>', resp.content.decode())), 2)

    def test_speaker_page_has_button_to_add_speech(self):
        # Add a speaker
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)

        # Call the speaker's page
        resp = self.client.get('/speaker/%s' % speaker.slug)

        self.assertContains(resp, '<a href="/speech/add?speaker=%d" class="button small right">Add speech</a>' % speaker.id, html=True)


    def test_speaker_headshots_in_speeches_section(self):
        # Test that headshots vs default image work OK
        self.speaker = speaker1 = Speaker.objects.create(
            name='Marilyn',
            instance=self.instance,
            summary='movie star',
            image=u'http://example.com/imag%C3%A9.jpg')
        speaker2 = Speaker.objects.create(name='Salinger',
            instance=self.instance)

        section = Section.objects.create(heading='Test Section',
            instance=self.instance)

        speech1 = Speech.objects.create(
            text="A girl doesn't need anyone that doesn't need her.",
            speaker=speaker1, section=section,
            instance=self.instance, public=True)

        speech2 = Speech.objects.create(
            text="I'm sick of not having the courage to be an absolute nobody.",
            speaker=speaker2, section=section,
            instance=self.instance, public=True)

        resp = self.client.get('/sections/' + str(section.id))

        assertRegex(self, resp.content.decode(), r'(?s)<img src="/uploads/speakers/default/imag%%C3%%A9.jpg.96x96_q85_crop-smart_face_upscale.jpg".*?<a href="/speaker/%s">\s*' % (speaker1.slug))
        assertRegex(self, resp.content.decode(), r'(?s)<img src="\s*/static/speeches/i/a.\w+.png\s*".*?<a href="/speaker/%s">\s*' % (speaker2.slug))

    def test_add_speaker_with_whitespace(self):
        name = ' Bob\n'
        self.client.post('/speaker/add', {'name': name})

        speaker = Speaker.objects.order_by('-id')[0]
        self.assertEqual(speaker.name, 'Bob')
