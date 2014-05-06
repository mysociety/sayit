import os
import tempfile
import shutil
import datetime

from django.test.utils import override_settings
from django.conf import settings

from speeches.tests import InstanceTestCase

import speeches
from speeches.models import Speech, Speaker, Section

TEMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SpeechTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')

    def tearDown(self):
        # Clear the speeches folder if it exists
        speeches_folder = os.path.join(settings.MEDIA_ROOT, 'speeches')
        if(os.path.exists(speeches_folder)):
            shutil.rmtree(speeches_folder)

    def test_add_speech_page_exists(self):
        # Test that the page exists and has the right title
        resp = self.client.get('/speech/add')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('Add a speech' in resp.content)

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
        self.assertRedirects(resp, '/speech/%d' % speech.id)
        self.assertEqual(speech.text, 'This is a speech')

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

        section = Section.objects.create(title='Test', instance=self.instance)
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
        self.assertContains( resp, 'Your speech has been <a href="/speech/%d">created</a>' % speech.id)
        self.assertContains( resp, 'in the section <a href="/%s#s%d">%s</a>!' % (
            section.slug, speech.id, section.title))

    def _post_speech(test, section, speech_data):
        post_data = speech_data.copy()
        try:
            post_data['start_date'] = speech_data['start_date'].strftime('%d/%m/%Y')
            post_data['end_date'] = speech_data['end_date'].strftime('%d/%m/%Y')
        except KeyError:
            pass
        resp = test.client.post('/speech/add', post_data)
        speech = Speech.objects.order_by('-id')[0]
        test.assertRedirects(resp, '/speech/add?section=%d&added=%d' % (section.id, speech.id))
        return resp

    def _check_initial_speech_data(test, response, section, speaker, speech_data):
        initial = response.context['form'].initial

        test.assertTrue('text' not in initial)

        test.assertEqual(initial['section'], section)
        test.assertEqual(initial['speaker'], speaker)
        for x in ['title', 'event', 'location', 'public', 'source_url', 'start_date', 'start_time']:
            test.assertEqual(initial.get(x, None), speech_data.get(x, None))

    def test_add_speech_metadata_in_section(self):
        section = Section.objects.create(title='Test', instance=self.instance)

        speakers = [Speaker.objects.create(name='Speaker %d' % i, instance=self.instance) for i in range(3)]

        speech_data = {
            'text':        'This is a speech',
            'section':     section.id,
            'title':       'Title',
            'event':       'Event',
            'location':    'Location',
            'speaker':     speakers[0].id,
            'public':      True,
            'source_url': 'http://example.com/speeches/1',
            'start_date': datetime.date(year=2000,month=1,day=15),
            'start_time': datetime.time(hour=12, minute=0, second=0),
            'add_another': 1,
        }

        _post = SpeechTests._post_speech
        _check_initial = SpeechTests._check_initial_speech_data
        form_url = '/speech/add?section=%d' % section.id

        resp = _post(self, section, speech_data)

        resp = self.client.get(form_url)
        speech_data['start_time'] = datetime.time(hour=12, minute=0, second=10)
        _check_initial(self, resp, section, speakers[0], speech_data)

        speech_data['speaker'] = speakers[1].id
        speech_data['end_date'] = speech_data['start_date']
        speech_data['end_time'] = datetime.time(hour=12, minute=0, second=30)
        resp = _post(self, section, speech_data)

        resp = self.client.get(form_url)
        speech_data['start_time'] = datetime.time(hour=12, minute=0, second=30)
        _check_initial(self, resp, section, speakers[0], speech_data)

        speech_data['speaker'] = speakers[2].id
        speech_data['start_time'] = datetime.time(hour=12, minute=0, second=30)
        speech_data['end_date'] = speech_data['start_date']
        speech_data['end_time'] = datetime.time(hour=12, minute=0, second=30)
        resp = _post(self, section, speech_data)

        resp = self.client.get(form_url)

        speech_data['start_time'] = datetime.time(hour=12, minute=0, second=31)
        _check_initial(self, resp, section, speakers[1], speech_data)

        # Test without start/end times
        del speech_data['start_date']
        del speech_data['start_time']
        del speech_data['end_date']
        del speech_data['end_time']
        speech_data['speaker'] = speakers[1].id
        resp = _post(self, section, speech_data)

        resp = self.client.get(form_url)
        _check_initial(self, resp, section, speakers[2], speech_data)

        # TODO: also default Tags

    def test_add_speech_metadata_start_date_but_no_time(self):
        section = Section.objects.create(title='Test', instance=self.instance)

        speakers = [Speaker.objects.create(name='Speaker %d' % i, instance=self.instance) for i in range(3)]

        speech_data = {
            'text':        'This is a speech',
            'section':     section.id,
            'title':       'Title',
            'event':       'Event',
            'location':    'Location',
            'speaker':     speakers[0].id,
            'public':      True,
            'source_url': 'http://example.com/speeches/1',
            'start_date': datetime.date(year=2000,month=1,day=15),
            'add_another': 1,
        }

        _post = SpeechTests._post_speech
        _check_initial = SpeechTests._check_initial_speech_data
        form_url = '/speech/add?section=%d' % section.id

        resp = _post(self, section, speech_data)

        resp = self.client.get(form_url)
        _check_initial(self, resp, section, speakers[0], speech_data)

        speech_data['speaker'] = speakers[1].id
        resp = _post(self, section, speech_data)

        resp = self.client.get(form_url)
        _check_initial(self, resp, section, speakers[0], speech_data)

        speech_data['speaker'] = speakers[0].id
        resp = _post(self, section, speech_data)

        resp = self.client.get(form_url)
        _check_initial(self, resp, section, speakers[1], speech_data)

    def test_add_speech_with_speaker(self):
        # Test form with speaker, we need to add a speaker first
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)

        resp = self.client.post('/speech/add', {
            'text': 'This is a Steve speech',
            'speaker': speaker.id
        })
        # Check in db
        speech = Speech.objects.get(speaker=speaker.id)
        self.assertEqual(speech.text, 'This is a Steve speech')

    def test_add_speech_with_audio(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')

        resp = self.client.post('/speech/add', {
            'audio': audio
        })
        # Assert that it uploads and we're told to wait
        speech = Speech.objects.order_by('-id')[0]
        resp = self.client.get('/speech/%d' % speech.id)
        self.assertContains( resp, 'recorded audio' )

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
        self.assertFalse('Please wait' in resp.content)
        self.assertTrue(text in resp.content)

        # Test edit page
        resp = self.client.get('/speech/%d/edit' % speech.id)

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
        self.assertRedirects(resp, '/speech/%d' % speech.id)
        self.assertEqual(speech.start_date, datetime.date(year=2000, month=1, day=1))
        self.assertIsNone(speech.start_time)
        self.assertEqual(speech.end_date, datetime.date(year=2000, month=1, day=1))
        self.assertIsNone(speech.end_time)

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
        self.assertRedirects(resp, '/speech/%d' % speech.id)
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

    def test_visible_speeches(self):
        section = Section.objects.create(title='Test', instance=self.instance)
        speeches = []
        for i in range(3):
            s = Speech.objects.create( text='Speech %d' % i, section=section, instance=self.instance, public=(i==2) )
            speeches.append(s)

        resp = self.client.get('/sections/%d' % section.id)
        self.assertEquals( [ x[0].public for x in resp.context['section_tree'] ], [ False, False, True ] )
        self.assertContains( resp, 'Invisible', count=2 )

        self.client.logout()
        resp = self.client.get('/speech/%d' % speeches[2].id)
        self.assertContains( resp, 'Speech 2' )
        resp = self.client.get('/speech/%d' % speeches[0].id)
        self.assertContains( resp, 'Not Found', status_code=404 )

    def test_speech_datetime_line(self):
        section = Section.objects.create(title='Test', instance=self.instance)
        Speech.objects.create( text='Speech', section=section, instance=self.instance,
            public=True, start_date=datetime.date(2000, 1, 1), end_date=datetime.date(2000, 1, 2)
        )

        resp = self.client.get('/sections/%d' % section.id)
        self.assertRegexpMatches( resp.content, '>\s+1 Jan 2000\s+&ndash;\s+2 Jan 2000\s+<' )

    def test_speech_page_has_buttons_to_edit(self):
        # Add a section
        speech = Speech.objects.create(text="A test speech", instance=self.instance)

        # Call the speech's page
        resp = self.client.get('/speech/%d' % speech.id)

        self.assertContains(resp, '<a href="/speech/%d/edit">Edit speech</a>' % speech.id, html=True)
        self.assertContains(resp, '<a href="/speech/%d/delete">Delete speech</a>' % speech.id, html=True)

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

        self.assertRedirects(resp, 'speeches')

        self.assertEqual(Speech.objects.filter(id=speech.id).count(), 0)
