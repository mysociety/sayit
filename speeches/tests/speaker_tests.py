import hashlib
import re
from datetime import date
from mock import patch, Mock
from six.moves.urllib.error import HTTPError

from django.test.utils import override_settings
from django.utils.six import assertRegex
from django.utils.encoding import smart_text

import lxml.html

from speeches.tests import InstanceTestCase, OverrideMediaRootMixin

from speeches.models import Speaker, Speech, Section
from speeches import models


def side_effect(url):
    if '404' in url:
        raise HTTPError(url, 404, 'NOT FOUND', None, None)
    return ('speeches/fixtures/test_inputs/Ferdinand_Magellan.jpg', None)


@override_settings(MEDIA_URL='/uploads/')
@patch.object(models, 'urlretrieve', Mock(side_effect=side_effect))
class SpeakerTests(OverrideMediaRootMixin, InstanceTestCase):
    """Tests for the speaker functionality"""
    speakers = []

    def tearDown(self):
        for speaker in self.speakers:
            speaker.image_cache.delete(save=False)

    def test_speaker_page_lists_speeches(self):
        # Add a speaker
        speaker = Speaker.objects.create(
            name='Steve', instance=self.instance,
            summary='A froody dude',
            image='http://example.com/image.jpg')
        self.speakers.append(speaker)
        id = ('%s' % speaker.person_ptr_id).encode()
        self.assertEqual(speaker.colour, hashlib.sha1(id).hexdigest()[:6])

        # Call the speaker's page
        resp = self.client.get('/speaker/%s' % speaker.slug)
        assertRegex(self, resp.content.decode(), r'background-color: #[0-9a-f]{6}(?i)')

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
        self.assertEqual(
            len(re.findall(r'<span class="breadcrumbs__date">\s*17 Sep 2014\s*</span>', resp.content.decode())), 2)

        # Add another speech on a different date and check the order
        speech = Speech.objects.create(
            text="A third speech",
            speaker=speaker,
            instance=self.instance,
            start_date=date(2014, 9, 18),
            )

        resp = self.client.get('/speaker/%s' % speaker.slug)
        self.assertEqual(resp.context['speech_list'][0].start_date, date(2014, 9, 18))

    def test_speaker_page_has_button_to_add_speech(self):
        # Add a speaker
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)

        # Call the speaker's page
        resp = self.client.get('/speaker/%s' % speaker.slug)

        self.assertContains(
            resp, '<a href="/speech/add?speaker=%d" class="button small right">Add speech</a>' % speaker.id, html=True)

    def test_speaker_headshots_in_speeches_section(self):
        # Test that headshots vs default image work OK
        speaker1 = Speaker.objects.create(
            name='Marilyn',
            instance=self.instance,
            summary='movie star',
            image=u'http://example.com/imag%C3%A9.jpg')
        self.speakers.append(speaker1)
        speaker2 = Speaker.objects.create(
            name='Salinger', instance=self.instance)

        section = Section.objects.create(
            heading='Test Section', instance=self.instance)

        Speech.objects.create(
            text="A girl doesn't need anyone that doesn't need her.",
            speaker=speaker1, section=section,
            instance=self.instance, public=True)

        Speech.objects.create(
            text="I'm sick of not having the courage to be an absolute nobody.",
            speaker=speaker2, section=section,
            instance=self.instance, public=True)

        resp = self.client.get('/section/' + str(section.id))

        assertRegex(
            self,
            resp.content.decode(),
            r'(?s)<img src="/uploads/speakers/default/imag%%C3%%A9.jpg.96x96_q85_crop-smart_face_upscale.jpg"'
            r'.*?<a href="/speaker/%s">\s*' % (speaker1.slug)
            )
        assertRegex(
            self,
            resp.content.decode(),
            r'(?s)<img src="\s*/static/speeches/i/a.png\s*".*?<a href="/speaker/%s">\s*' % (speaker2.slug)
            )

    def test_create_speaker_with_long_image_url(self):
        sixtyfive = '1234567890' * 6 + '12345'
        ninetynine = '1234567890' * 9 + '123456789'
        long_image_url = 'http://example.com/image%%E1%%BD%%A0%s.jpg' % ninetynine

        s1 = Speaker.objects.create(
            name='Long Image URL',
            instance=self.instance,
            image=long_image_url,
            )
        s2 = Speaker.objects.create(
            name='Duplicate long image URL',
            instance=self.instance,
            image=long_image_url,
            )
        self.speakers.extend((s1, s2))

        # Note the filename in image_cache has been truncated.
        self.assertEqual(
            s1.image_cache,
            u'speakers/default/image\u1f60%s.jpg' % sixtyfive,
            )

        # The truncated filename for the second speaker has some random stuff at the end.
        # If this get fails it might well mean you need a Django security update
        # https://www.djangoproject.com/weblog/2014/aug/20/security/
        assertRegex(
            self,
            smart_text(s2.image_cache),
            u'^speakers/default/image\u1f60%s_.{7}\.jpg$' % sixtyfive,
            )

    def test_add_speaker_with_whitespace(self):
        name = ' Bob\n'
        self.client.post('/speaker/add', {'name': name})

        speaker = Speaker.objects.order_by('-id')[0]
        self.assertEqual(speaker.name, 'Bob')

    def test_add_speaker_with_image_not_found(self):
        try:
            Speaker.objects.create(
                name='Not Found',
                instance=self.instance,
                image='http://httpbin.org/status/404')
        except HTTPError:
            self.fail("Speaker unexpectedly raised HTTPError")

    def test_speaker_list_ordering(self):
        Speaker.objects.create(name='alice', instance=self.instance)
        Speaker.objects.create(name='Bob', instance=self.instance)
        Speaker.objects.create(name='Eve', sort_name='AAA FIRST', instance=self.instance)
        resp = self.client.get('/speakers')
        assertRegex(self, resp.content.decode(), u'Eve.*alice.*Bob(?s)')


class MergeDeleteSpeakerTests(InstanceTestCase):
    def test_no_speeches(self):
        alice = Speaker.objects.create(name='alice', instance=self.instance)
        alice_id = alice.id

        resp = self.client.get('/speaker/%d/delete' % alice_id)
        self.assertContains(resp, 'Delete speaker: alice')

        parser = lxml.html.HTMLParser(encoding='utf-8')
        root = lxml.html.fromstring(resp.content, parser=parser)

        # Check that we have been shown the short form without action
        # and new speaker
        self.assertEquals(len(root.xpath(".//select[@name='action']")), 0)
        self.assertEquals(len(root.xpath(".//input[@name='new_speaker']")), 0)

        resp = self.client.post('/speaker/%d/delete' % alice_id)
        self.assertRedirects(resp, '/speakers')

        self.assertEqual(Speaker.objects.filter(id=alice_id).count(), 0)

    def test_with_speeches(self):
        alice = Speaker.objects.create(name='alice', instance=self.instance)
        alice.speech_set.create(text='Test', instance=self.instance)

        resp = self.client.get('/speaker/%d/delete' % alice.id)
        self.assertContains(resp, 'Delete speaker: alice')
        parser = lxml.html.HTMLParser(encoding='utf-8')
        root = lxml.html.fromstring(resp.content, parser=parser)

        # Check that we have been shown the form with an action and
        # a new speaker to choose.
        self.assertEquals(len(root.xpath(".//input[@name='action'][@type='radio']")), 3)
        self.assertEquals(len(root.xpath(".//input[@name='new_speaker']")), 1)

    def test_remove_speeches(self):
        alice = Speaker.objects.create(name='alice', instance=self.instance)
        alice_id = alice.id
        alice.speech_set.create(text='Test', instance=self.instance)

        resp = self.client.post(
            '/speaker/%d/delete' % alice_id,
            {'action': 'Delete'},
            )
        self.assertEqual(Speaker.objects.filter(id=alice_id).count(), 0)
        self.assertEqual(Speech.objects.count(), 0)
        self.assertRedirects(resp, '/speakers')

    def test_orphan_speeches(self):
        alice = Speaker.objects.create(name='alice', instance=self.instance)
        alice_id = alice.id
        alice.speech_set.create(text='Test', instance=self.instance)

        resp = self.client.post(
            '/speaker/%d/delete' % alice_id,
            {'action': 'Narrative'},
            )
        self.assertEqual(Speaker.objects.filter(id=alice_id).count(), 0)
        self.assertEqual(Speech.objects.filter(type='narrative').count(), 1)
        self.assertEqual(Speech.objects.filter(speaker=alice).count(), 0)
        self.assertRedirects(resp, '/speakers')

    def test_reassign_speeches(self):
        alice = Speaker.objects.create(name='alice', instance=self.instance)
        bob = Speaker.objects.create(name='bob', instance=self.instance)
        alice_id = alice.id
        alice.speech_set.create(text='Test', instance=self.instance)

        resp = self.client.post(
            '/speaker/%d/delete' % alice_id,
            {'action': 'Reassign', 'new_speaker': bob.id},
            )
        self.assertEqual(Speaker.objects.filter(id=alice_id).count(), 0)
        self.assertEqual(Speech.objects.filter(speaker=bob).count(), 1)
        self.assertEqual(Speech.objects.filter(speaker=alice).count(), 0)
        self.assertRedirects(resp, '/speakers')

    def test_reassign_with_no_new_speaker(self):
        alice = Speaker.objects.create(name='alice', instance=self.instance)
        Speaker.objects.create(name='bob', instance=self.instance)
        alice_id = alice.id
        alice.speech_set.create(text='Test', instance=self.instance)

        resp = self.client.post(
            '/speaker/%d/delete' % alice_id,
            {'action': 'Reassign'},
            )
        self.assertFormError(
            resp, 'form', 'new_speaker',
            'You must choose a new speaker if reassigning speeches')

    def test_delete_or_merge_speeches_with_new_speaker(self):
        alice = Speaker.objects.create(name='alice', instance=self.instance)
        bob = Speaker.objects.create(name='bob', instance=self.instance)
        alice_id = alice.id
        alice.speech_set.create(text='Test', instance=self.instance)

        resp = self.client.post(
            '/speaker/%d/delete' % alice_id,
            {'action': 'Delete', 'new_speaker': bob.id},
            )
        self.assertFormError(
            resp, 'form', 'new_speaker',
            'You must not choose a new speaker unless reassigning speeches')

        resp = self.client.post(
            '/speaker/%d/delete' % alice_id,
            {'action': 'Narrative', 'new_speaker': bob.id},
            )
        self.assertFormError(
            resp, 'form', 'new_speaker',
            'You must not choose a new speaker unless reassigning speeches')

    def test_assign_to_same_speaker(self):
        alice = Speaker.objects.create(name='alice', instance=self.instance)
        alice_id = alice.id
        alice.speech_set.create(text='Test', instance=self.instance)

        resp = self.client.post(
            '/speaker/%d/delete' % alice_id,
            {'action': 'Reassign', 'new_speaker': alice_id},
            )
        self.assertFormError(
            resp, 'form', 'new_speaker',
            "You can't assign speeches to the speaker you're deleting")
