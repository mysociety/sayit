import os
import tempfile
import shutil
import re
import datetime

from django.test.utils import override_settings
from django.conf import settings

from speeches.tests import InstanceTestCase

import speeches
from speeches.models import Speech, Speaker, Section

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SpeechFormTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')
        super(SpeechFormTests, cls).setUpClass()

    def tearDown(self):
        # Clear the speeches folder if it exists
        speeches_folder = os.path.join(settings.MEDIA_ROOT, 'speeches')
        if(os.path.exists(speeches_folder)):
            shutil.rmtree(speeches_folder)

    def test_add_speech_page_exists(self):
        # Test that the page exists and has the right title
        resp = self.client.get('/speech/add')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('Add a speech' in resp.content.decode())

    def test_add_speech_fails_on_empty_form(self):
        # Test that the form won't submit if empty
        resp = self.client.post('/speech/add')
        self.assertFormError(resp, 'form', None, 'You must provide either text or some audio')

    def test_add_speech_without_speaker(self):
        # Test form without speaker
        resp = self.client.post('/speech/add', {
            'text': 'This is a speech'
        })
        speech = Speech.objects.order_by('-id')[0]
        self.assertRedirects(resp, '/speech/%d?created' % speech.id)
        self.assertEqual(speech.text, 'This is a speech')
        self.assertEqual(speech.speaker, None)
        self.assertEqual(speech.type, 'narrative')

    def test_add_speech_with_unknown_speaker(self):
        """Try adding a speech with a speaker not yet in the database.

        Adding a speech with a speaker name which is unknown to us should cause
        that speaker to be created.
        """
        self.assertEqual(Speaker.objects.filter(name='New Speaker').count(), 0)
        # Note whitespace around speaker name to check it is stripped
        self.client.post(
            '/speech/add',
            {'text': 'Speech from new speaker',
             'speaker': ' New Speaker '},
            )

        speaker = Speaker.objects.get(name='New Speaker')
        speech = Speech.objects.order_by('-id')[0]
        self.assertEqual(speech.text, '<p>Speech from new speaker</p>')
        self.assertEqual(speech.speaker, speaker)
        self.assertEqual(speech.type, 'speech')

    def test_add_speech_with_unknown_data_and_bad_form(self):
        """Try adding a speech with new speaker/section and no other data.

        What we want to happen in this case is for the new data
        to be created, and the form given back to the user to
        correct the other error with the new data displayed
        correctly.
        """

        self.assertEqual(Speaker.objects.filter(name='New Bod').count(), 0)
        self.assertEqual(Section.objects.filter(heading='New Section').count(), 0)

        resp = self.client.post('/speech/add', {'speaker': 'New Bod', 'section': 'New Section'})

        self.assertEqual(Speaker.objects.filter(name='New Bod').count(), 1)
        self.assertEqual(Section.objects.filter(heading='New Section').count(), 1)
        self.assertContains(resp, '.txt(["New Bod"])')
        self.assertContains(resp, '.txt(["New Section"])')
        self.assertContains(resp, "You must provide either text or some audio")

    def test_add_speech_with_unknown_section(self):
        """Try adding a speech with a section not yet in the database.

        Adding a speech with a section which is unknown to us should cause
        that section to be created.
        """
        self.assertEqual(Section.objects.filter(heading='New Section').count(), 0)
        self.client.post(
            '/speech/add',
            {'text': 'Speech in new section', 'section': 'New Section'},
        )

        section = Section.objects.get(heading='New Section')
        speech = Speech.objects.order_by('-id')[0]
        self.assertEqual(speech.text, 'Speech in new section')
        self.assertEqual(speech.section, section)

    def test_add_speech_and_add_another(self):
        # Test form with 'add_another' but without a section
        # (client JS will prevent this case from happening, in general)
        resp = self.client.post('/speech/add', {
            'text': 'This is a speech',
            'add_another': 1,
        })
        speech = Speech.objects.order_by('-id')[0]
        self.assertEqual(speech.text, 'This is a speech')
        self.assertRedirects(resp, '/speech/add')

        section = Section.objects.create(heading='Test', instance=self.instance)
        resp = self.client.post('/speech/add', {
            'text': 'This is a speech',
            'section': section.id,
            'add_another': 1,
        })
        speech = Speech.objects.order_by('-id')[0]
        self.assertEqual(speech.text, 'This is a speech')
        self.assertEqual(speech.section_id, section.id)
        get_url = '/speech/add?section=%d&added=%d' % (section.id, speech.id)
        self.assertRedirects(resp, get_url)

        resp = self.client.get(get_url)
        self.assertContains(resp, 'Your speech has been <a href="/speech/%d">created</a>' % speech.id)
        self.assertContains(resp, 'in the section <a href="/%s#s%d">%s</a>!' % (
            section.slug, speech.id, section.heading))

    def _post_speech(self, section, speech_data):
        post_data = speech_data.copy()
        try:
            post_data['start_date'] = speech_data['start_date'].strftime('%d/%m/%Y')
            post_data['end_date'] = speech_data['end_date'].strftime('%d/%m/%Y')
        except KeyError:
            pass
        resp = self.client.post('/speech/add', post_data)
        speech = Speech.objects.order_by('-id')[0]
        self.assertRedirects(resp, '/speech/add?section=%d&added=%d' % (section.id, speech.id))
        return resp

    def _check_initial_speech_data(self, response, section, speaker, speech_data):
        initial = response.context['form'].initial

        self.assertTrue('text' not in initial)

        self.assertEqual(initial['section'], section)
        self.assertEqual(initial['speaker'], speaker)
        for x in ['heading', 'event', 'location', 'public', 'source_url', 'start_date', 'start_time']:
            self.assertEqual(initial.get(x, None), speech_data.get(x, None))

    def test_add_speech_metadata_in_section(self):
        section = Section.objects.create(heading='Test', instance=self.instance)

        speakers = [Speaker.objects.create(name='Speaker %d' % i, instance=self.instance) for i in range(3)]

        speech_data = {
            'text': 'This is a speech',
            'section': section.id,
            'heading': 'Title',
            'event': 'Event',
            'location': 'Location',
            'speaker': speakers[0].id,
            'public': True,
            'source_url': 'http://example.com/speeches/1',
            'start_date': datetime.date(year=2000, month=1, day=15),
            'start_time': datetime.time(hour=12, minute=0, second=0),
            'add_another': 1,
        }

        form_url = '/speech/add?section=%d' % section.id

        resp = self._post_speech(section, speech_data)

        resp = self.client.get(form_url)
        speech_data['start_time'] = datetime.time(hour=12, minute=0, second=10)
        self._check_initial_speech_data(resp, section, speakers[0], speech_data)

        speech_data['speaker'] = speakers[1].id
        speech_data['end_date'] = speech_data['start_date']
        speech_data['end_time'] = datetime.time(hour=12, minute=0, second=30)
        resp = self._post_speech(section, speech_data)

        resp = self.client.get(form_url)
        speech_data['start_time'] = datetime.time(hour=12, minute=0, second=30)
        self._check_initial_speech_data(resp, section, speakers[0], speech_data)

        speech_data['speaker'] = speakers[2].id
        speech_data['start_time'] = datetime.time(hour=12, minute=0, second=30)
        speech_data['end_date'] = speech_data['start_date']
        speech_data['end_time'] = datetime.time(hour=12, minute=0, second=30)
        resp = self._post_speech(section, speech_data)

        resp = self.client.get(form_url)

        speech_data['start_time'] = datetime.time(hour=12, minute=0, second=31)
        self._check_initial_speech_data(resp, section, speakers[1], speech_data)

        # Test without start/end times
        del speech_data['start_date']
        del speech_data['start_time']
        del speech_data['end_date']
        del speech_data['end_time']
        speech_data['speaker'] = speakers[1].id
        resp = self._post_speech(section, speech_data)

        resp = self.client.get(form_url)
        self._check_initial_speech_data(resp, section, speakers[2], speech_data)

        # TODO: also default Tags

    def test_add_speech_metadata_start_date_but_no_time(self):
        section = Section.objects.create(heading='Test', instance=self.instance)

        speakers = [Speaker.objects.create(name='Speaker %d' % i, instance=self.instance) for i in range(3)]

        speech_data = {
            'text': 'This is a speech',
            'section': section.id,
            'heading': 'Title',
            'event': 'Event',
            'location': 'Location',
            'speaker': speakers[0].id,
            'public': True,
            'source_url': 'http://example.com/speeches/1',
            'start_date': datetime.date(year=2000, month=1, day=15),
            'add_another': 1,
        }

        form_url = '/speech/add?section=%d' % section.id

        resp = self._post_speech(section, speech_data)

        resp = self.client.get(form_url)
        self._check_initial_speech_data(resp, section, speakers[0], speech_data)

        speech_data['speaker'] = speakers[1].id
        resp = self._post_speech(section, speech_data)

        resp = self.client.get(form_url)
        self._check_initial_speech_data(resp, section, speakers[0], speech_data)

        speech_data['speaker'] = speakers[0].id
        resp = self._post_speech(section, speech_data)

        resp = self.client.get(form_url)
        self._check_initial_speech_data(resp, section, speakers[1], speech_data)

    def test_add_speech_with_speaker(self):
        # Test form with speaker, we need to add a speaker first
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)

        resp = self.client.post('/speech/add', {
            'text': 'This is a Steve speech',
            'speaker': speaker.id
        })
        # Check in db
        speech = Speech.objects.get(speaker=speaker.id)
        self.assertEqual(speech.text, '<p>This is a Steve speech</p>')
        self.assertEqual(speech.type, 'speech')

        # Check that the edit page for this speech contains the speaker's name
        resp = self.client.get('/speech/{}/edit'.format(speech.id))
        self.assertContains(resp, '.txt(["Steve"])')

    def test_add_and_remove_speaker_from_speech(self):
        # Test form with speaker, we need to add a speaker first
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)

        orig_text = 'This is a Steve speech\nAfter break\n\nNew paragraph'
        with_speaker_text = '<p>This is a Steve speech<br />After break</p>\n\n<p>New paragraph</p>'
        no_speaker_text = 'This is a Steve speech<br />After break<br />\nNew paragraph'

        resp = self.client.post('/speech/add', {
            'text': orig_text,
            'speaker': speaker.id,
        })

        speech = Speech.objects.get(speaker_id=speaker.id)
        self.assertEqual(speech.text, with_speaker_text)
        self.assertEqual(speech.type, 'speech')

        resp = self.client.get('/speech/{}/edit'.format(speech.id))
        self.assertTrue(orig_text in resp.content.decode())

        self.client.post(
            '/speech/{}/edit'.format(speech.id),
            {'text': orig_text},
            )

        speech = Speech.objects.get(id=speech.id)
        self.assertEqual(speech.text, no_speaker_text)
        self.assertEqual(speech.type, 'narrative')

        resp = self.client.get('/speech/{}/edit'.format(speech.id))
        self.assertTrue(orig_text in resp.content.decode())

        self.client.post(
            '/speech/{}/edit'.format(speech.id),
            {'text': orig_text, 'speaker': speaker.id},
            )

        speech = Speech.objects.get(speaker_id=speaker.id)
        self.assertEqual(speech.text, with_speaker_text)
        self.assertEqual(speech.type, 'speech')

    def test_add_speech_with_audio(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')

        resp = self.client.post('/speech/add', {
            'audio': audio
        })
        # Assert that it uploads and we're told to wait
        speech = Speech.objects.order_by('-id')[0]
        resp = self.client.get('/speech/%d' % speech.id)
        self.assertContains(resp, 'recorded audio')

        # Assert that it's in the model
        self.assertIsNotNone(speech.audio)

    def test_add_speech_with_audio_and_text(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')
        text = 'This is a speech with some text'

        resp = self.client.post('/speech/add', {
            'audio': audio,
            'text': text
        })

        # Assert that it uploads and we see it straightaway
        speech = Speech.objects.order_by('-id')[0]
        resp = self.client.get('/speech/%d' % speech.id)
        self.assertFalse('Please wait' in resp.content.decode('utf-8'))
        self.assertTrue(text in resp.content.decode('utf-8'))

        # Test edit page
        resp = self.client.get('/speech/%d/edit' % speech.id)

    def test_add_speech_with_whitespace_around_text(self):
        text = ' This is a speech with whitespace at the ends. '
        self.client.post('/speech/add', {'text': text})

        speech = Speech.objects.order_by('-id')[0]
        self.assertEqual(speech.text, 'This is a speech with whitespace at the ends.')

    def test_add_speech_with_newlines(self):
        text = "First line.\nAfter break.\n\nAfter another break."
        self.client.post('/speech/add', {'text': text})
        speech = Speech.objects.order_by('-id')[0]
        self.assertEqual(
            speech.text,
            'First line.<br />After break.<br />\nAfter another break.'
            )

        resp = self.client.get("/speech/%d/edit" % speech.id)
        self.assertContains(resp, text)

    def test_add_speech_with_newlines_and_speaker(self):
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)
        text = "First line.\nAfter break.\n\nNew paragraph."
        self.client.post(
            '/speech/add',
            {'text': text, 'speaker': speaker.id},
            )
        speech = Speech.objects.order_by('-id')[0]
        self.assertEqual(
            speech.text,
            '<p>First line.<br />After break.</p>\n\n<p>New paragraph.</p>'
            )

        resp = self.client.get("/speech/%d/edit" % speech.id)
        self.assertContains(resp, text)

    def test_add_speech_with_html(self):
        """If a user adds a speech which starts with a <p>, we're going to have
        to take those out, as Akoma Ntoso doesn't allow them in <narrative> elemnts.

        What we do want to do though is make sure that every </p> is followed by two
        newlines (\n) so that when we take the <p>s etc out to edit we can see where
        to put them back in again.
        """

        text = "<p>Test<br />string</p><p>Second paragraph</p>\n<p>Third paragraph</p>\n\n<p>Fourth paragraph</p>"
        self.client.post('/speech/add', {'text': text})
        speech = Speech.objects.order_by('-id')[0]
        self.assertEqual(
            speech.text,
            "Test<br />string<br />\nSecond paragraph<br />\nThird paragraph<br />\nFourth paragraph"
            )

    def test_add_speech_with_html_and_speaker(self):
        """If a user adds a speech which starts with a <p>, we probably
        don't want to add more <p>s to it.

        What we do want to do though is make sure that every </p> is followed by two
        newlines (\n) so that when we take the <p>s etc out to edit we can see where
        to put them back in again.
        """
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)
        text = "<p>Test<br />string</p><p>Second paragraph</p>\n<p>Third paragraph</p>\n\n<p>Fourth paragraph</p>"
        self.client.post('/speech/add', {'text': text, 'speaker': speaker.id})
        speech = Speech.objects.order_by('-id')[0]
        self.assertEqual(
            speech.text,
            "<p>Test<br />string</p>\n\n<p>Second paragraph</p>\n\n<p>Third paragraph</p>\n\n<p>Fourth paragraph</p>"
            )

    def test_add_speech_fails_with_unsupported_audio(self):
        # Load the .aiff fixture
        audio = open(os.path.join(self._in_fixtures, 'lamb.aiff'), 'rb')

        resp = self.client.post('/speech/add', {
            'audio': audio
        })

        # Assert that it fails and gives us an error
        self.assertFormError(resp, 'form', 'audio', 'That file does not appear to be an audio file')

    def test_add_speech_with_dates_only(self):
        # Test form with dates (but not times)
        resp = self.client.post('/speech/add', {
            'text': 'This is a speech',
            'start_date': '01/01/2000',
            'end_date': '01/01/2000'
        })
        speech = Speech.objects.order_by('-id')[0]
        self.assertRedirects(resp, '/speech/%d?created' % speech.id)
        self.assertEqual(speech.start_date, datetime.date(year=2000, month=1, day=1))
        self.assertIsNone(speech.start_time)
        self.assertEqual(speech.end_date, datetime.date(year=2000, month=1, day=1))
        self.assertIsNone(speech.end_time)

    def test_add_speech_form_internationalization(self):
        en_gb_language_headers = {'HTTP_ACCEPT_LANGUAGE': 'en-GB'}
        en_language_headers = {'HTTP_ACCEPT_LANGUAGE': 'en'}

        en_gb_resp = self.client.get('/speech/add', **en_gb_language_headers)
        self.assertContains(en_gb_resp, 'placeholder="dd/mm/yyyy"')

        resp = self.client.post(
            '/speech/add',
            {'text': 'This is a speech',
             'start_date': '20/01/2000',
             'end_date': '21/01/2000'},
            **en_gb_language_headers)

        speech = Speech.objects.order_by('-id')[0]
        self.assertRedirects(resp, '/speech/%d?created' % speech.id)
        self.assertEqual(speech.start_date, datetime.date(year=2000, month=1, day=20))
        self.assertEqual(speech.end_date, datetime.date(year=2000, month=1, day=21))

        en_resp = self.client.get('/speech/add', **en_language_headers)
        self.assertContains(en_resp, 'placeholder="yyyy-mm-dd"')

        # With language 'en', the default format is ISO8601
        resp = self.client.post(
            '/speech/add',
            {'text': 'This is a speech',
             'start_date': '2000-01-20',
             'end_date': '2000-01-21'},
            **en_language_headers)

        speech = Speech.objects.order_by('-id')[0]
        self.assertRedirects(resp, '/speech/%d?created' % speech.id)
        self.assertEqual(speech.start_date, datetime.date(year=2000, month=1, day=20))
        self.assertEqual(speech.end_date, datetime.date(year=2000, month=1, day=21))

        # With language 'en', django will also handle dates in the US back to
        # front fashion.
        resp = self.client.post(
            '/speech/add',
            {'text': 'This is a speech',
             'start_date': '01/20/2000',
             'end_date': '01/21/2000'},
            **en_language_headers)

        speech = Speech.objects.order_by('-id')[0]
        self.assertRedirects(resp, '/speech/%d?created' % speech.id)
        self.assertEqual(speech.start_date, datetime.date(year=2000, month=1, day=20))
        self.assertEqual(speech.end_date, datetime.date(year=2000, month=1, day=21))

    def test_add_speech_with_dates_and_times(self):
        # Test form with dates (but not times)
        resp = self.client.post('/speech/add', {
            'text': 'This is a speech',
            'start_date': '01/01/2000',
            'start_time': '12:45',
            'end_date': '01/01/2000',
            'end_time': '17:53'
        })
        speech = Speech.objects.order_by('-id')[0]
        self.assertRedirects(resp, '/speech/%d?created' % speech.id)
        self.assertEqual(speech.start_date, datetime.date(year=2000, month=1, day=1))
        self.assertEqual(speech.start_time, datetime.time(hour=12, minute=45))
        self.assertEqual(speech.end_date, datetime.date(year=2000, month=1, day=1))
        self.assertEqual(speech.end_time, datetime.time(hour=17, minute=53))

    def test_add_speech_fails_with_times_only(self):
        # Test form with dates (but not times)
        resp = self.client.post('/speech/add', {
            'text': 'This is a speech',
            'start_time': '12:45',
            'end_time': '17:53'
        })
        self.assertFormError(resp, 'form', 'start_time', 'If you provide a start time you must give a start date too')
        self.assertFormError(resp, 'form', 'end_time', 'If you provide an end time you must give an end date too')

    def test_add_speech_with_audio_encodes_to_mp3(self):
        # Load the wav fixture
        audio = open(os.path.join(self._in_fixtures, 'lamb_stereo.wav'), 'rb')

        resp = self.client.post('/speech/add', {
            'audio': audio
        })

        # Assert that it uploads
        speech = Speech.objects.order_by('-id')[0]
        resp = self.client.get('/speech/%d' % speech.id)
        self.assertContains(resp, 'recorded audio')

        self.assertIsNotNone(speech.audio)
        self.assertTrue(".mp3" in speech.audio.path)


class SpeechViewTests(InstanceTestCase):
    def test_speech_heading_display(self):
        speech = Speech.objects.create(
            text='Speech text',
            heading='Speech title',
            instance=self.instance,
            start_date=datetime.date(2014, 9, 17),
            )
        resp = self.client.get('/speech/%d' % speech.id)
        self.assertContains(resp, '<h1>Speech title</h1>')
        resp = self.client.get('/speeches')
        self.assertContains(resp, 'Speech title')

        # Check that two speeches on the same date both have their date displayed
        Speech.objects.create(
            text='Another speech',
            instance=self.instance,
            start_date=datetime.date(2014, 9, 17),
            )

        resp = self.client.get('/speeches')
        assert len(re.findall(
            r'<span class="speech__meta-data__date">\s*17 Sep 2014\s*</span>',
            resp.content.decode())) == 2

        section = Section.objects.create(heading='Test', instance=self.instance)
        speech.section = section
        speech.save()
        resp = self.client.get('/section/%d' % section.id)
        self.assertContains(resp, 'Speech title')

    def test_visible_speeches(self):
        section = Section.objects.create(heading='Test', instance=self.instance)
        speeches = []
        for i in range(3):
            s = Speech.objects.create(text='Speech %d' % i, section=section, instance=self.instance, public=(i == 2))
            speeches.append(s)

        resp = self.client.get('/section/%d' % section.id)
        self.assertEqual([x[0].public for x in resp.context['section_tree']], [False, False, True])
        self.assertContains(resp, 'Invisible', count=2)

        self.client.logout()
        resp = self.client.get('/speech/%d' % speeches[2].id)
        self.assertContains(resp, 'Speech 2')
        resp = self.client.get('/speech/%d' % speeches[0].id)
        self.assertContains(resp, 'Not Found', status_code=404)

    def test_speech_datetime_line(self):
        section = Section.objects.create(heading='Test', instance=self.instance)
        Speech.objects.create(
            text='Speech', section=section, instance=self.instance,
            public=True, start_date=datetime.date(2000, 1, 1), end_date=datetime.date(2000, 1, 2)
        )

        resp = self.client.get('/section/%d' % section.id)
        self.assertRegexpMatches(resp.content.decode(), '>\s+1 Jan 2000\s+&ndash;\s+2 Jan 2000\s+<')

    def test_speech_page_has_buttons_to_edit(self):
        # Add a section
        speech = Speech.objects.create(text="A test speech", instance=self.instance)

        # Call the speech's page
        resp = self.client.get('/speech/%d' % speech.id)

        self.assertContains(
            resp, '<a href="/speech/%d/edit"><i class="speech-icon icon-edit"></i>Edit</a>' % speech.id, html=True)
        self.assertContains(
            resp, '<a href="/speech/%d/delete"><i class="speech-icon icon-delete"></i>Delete</a>' % speech.id,
            html=True)

    def test_speech_deletion(self):
        # Set up the section
        speech = Speech.objects.create(text="A test speech", instance=self.instance)
        resp = self.client.get('/speech/%d' % speech.id)

        # GET form (confirmation page)
        resp = self.client.get(speech.get_delete_url())
        self.assertContains(resp, '<input type="submit" value="Confirm delete?"')

        speech_db = Speech.objects.get(id=speech.id)
        self.assertEqual(speech_db.id, speech.id)

        # POST form (do the deletion)
        resp = self.client.post(speech.get_delete_url())

        self.assertRedirects(resp, '/speeches')

        self.assertEqual(Speech.objects.filter(id=speech.id).count(), 0)


class SpeechTests(InstanceTestCase):
    def test_speech_with_i18n(self):
        speaker = Speaker.objects.create(name=u'Beyonc\u00e9', instance=self.instance)
        speech = Speech.objects.create(
            heading=u'D\u00e9j\u00e0 Vu', text='Bass', speaker=speaker, instance=self.instance)
        self.assertEqual(u'%s' % speech, u'Speech, D\u00e9j\u00e0 Vu by Beyonc\u00e9 (with text)')
