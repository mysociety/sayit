import sys
from mock import patch, Mock, mock_open

import django
from django.utils.six import assertRegex
from django.utils.six.moves import builtins
from easy_thumbnails.templatetags import thumbnail

from speeches.tests import InstanceTestCase
from speeches.models import Speaker, Speech, Section
from speeches import models


class SpeakerTests(InstanceTestCase):
    """Tests for the speaker functionality"""

    def test_speaker_page_lists_speeches(self):
        mock = mock_open()
        mock.return_value.size = 1000 # Needed to pass
        with patch.object(models, 'urlretrieve', return_value=('foo/tempfile.jpg', None)), \
             patch('django.core.files.storage.Storage.save', return_value='speakers/default/image.jpg'), \
             patch.object(builtins, 'open', mock):
            # Add a speaker
            speaker = Speaker.objects.create(name='Steve', instance=self.instance, summary='A froody dude', image='http://example.com/image.jpg')

        # Call the speaker's page
        resp = self.client.get('/speaker/%s' % speaker.slug)

        self.assertSequenceEqual("Steve", resp.context['speaker'].name)
        self.assertSequenceEqual("A froody dude", resp.context['speaker'].summary)
        self.assertSequenceEqual("http://example.com/image.jpg", resp.context['speaker'].image)

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

        self.assertContains(resp, '<a href="/speech/add?speaker=%d" class="button small right">Add speech</a>' % speaker.id, html=True)


    def test_speaker_headshots_in_speeches_section(self):
        mock = mock_open()
        mock.return_value.size = 1000 # Needed to pass
        with patch.object(models, 'urlretrieve', return_value=('foo/tempfile.jpg', None)), \
             patch('django.core.files.storage.Storage.save', return_value='speakers/default/image.jpg'), \
             patch.object(builtins, 'open', mock):

            # Test that headshots vs default image work OK
            speaker1 = Speaker.objects.create(name='Marilyn', instance=self.instance, summary='movie star', image='http://example.com/image.jpg')
            speaker2 = Speaker.objects.create(name='Salinger', instance=self.instance)

        section = Section.objects.create(heading='Test Section', instance=self.instance)

        speech1 = Speech.objects.create( text="A girl doesn't need anyone that doesn't need her.", speaker=speaker1, section=section, instance=self.instance, public=True )

        speech2 = Speech.objects.create( text="I'm sick of not having the courage to be an absolute nobody.", speaker=speaker2, section=section, instance=self.instance, public=True )

        with patch('easy_thumbnails.templatetags.thumbnail.get_thumbnailer',
                 Mock(return_value={'speaker-thumb': Mock(url='/uploads/speakers/default/image.jpg')})
                 ):
            resp = self.client.get('/sections/' + str(section.id))

            assertRegex(self, resp.content.decode(), r'(?s)<img src="/uploads/speakers/default/image.jpg".*?<a href="/speaker/%s">\s*' % (speaker1.slug))
            assertRegex(self, resp.content.decode(), r'(?s)<img src="\s*/static/speeches/i/a.\w+.png\s*".*?<a href="/speaker/%s">\s*' % (speaker2.slug))

    def test_add_speaker_with_whitespace(self):
        name = ' Bob\n'
        self.client.post('/speaker/add', {'name': name})

        speaker = Speaker.objects.order_by('-id')[0]
        self.assertEqual(speaker.name, 'Bob')
