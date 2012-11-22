"""
Testing of the speeches app.
Testing documentation is at https://docs.djangoproject.com/en/1.4/topics/testing/
"""

from django.test import TestCase

from speeches.models import Speech

class SpeechTest(TestCase):
    def test_add_speech(self):
        resp = self.client.get('/speech/add')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('add a new speech' in resp.content)

        resp = self.client.post('/speech/add')
        self.assertFormError(resp, 'form', None, 'You must provide either text or some audio')

        resp = self.client.post('/speech/add', {
            'text': 'This is a speech',
            'speaker': 'Matthew',
        })
        self.assertRedirects(resp, '/speech/1')

        # Check in db
        speech = Speech.objects.get(speaker='Matthew')
        self.assertEqual(speech.text, 'This is a speech')

        # Test file upload, audio
        # Use LiveServerTestCase


