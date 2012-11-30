"""
Testing of the speeches app.
Testing documentation is at https://docs.djangoproject.com/en/1.4/topics/testing/
"""

from selenium import webdriver

from django.test import TestCase, LiveServerTestCase

from speeches.models import Speech, Speaker

class SpeechTest(TestCase):
    def test_add_speech_page_exists(self):
        # Test that the page exists and has the right title
        resp = self.client.get('/speech/add')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('add a new speech' in resp.content)

    def test_add_speech_fails_on_empty_form(self):
        # Test that the form won't submit if empty
        resp = self.client.post('/speech/add')
        self.assertFormError(resp, 'form', None, 'You must provide either text or some audio')

    def test_add_speech_without_speaker(self):
        # Test form without speaker
        resp = self.client.post('/speech/add', {
            'text': 'This is a speech'
        })
        self.assertRedirects(resp, '/speech/1')
        # Check in db
        speech = Speech.objects.get(id=1)
        self.assertEqual(speech.text, 'This is a speech')

    def test_add_speech_with_speaker(self):
        # Test form with speaker, we need to add a speaker first
        speaker = Speaker.objects.create(popit_id='abcd', name='Steve')
        resp = self.client.post('/speech/add', {
            'text': 'This is a Steve speech',
            'speaker': speaker.id
        })
        self.assertRedirects(resp, '/speech/1')
        # Check in db
        speech = Speech.objects.get(speaker=speaker.id)
        self.assertEqual(speech.text, 'This is a Steve speech')

        # Test file upload, audio
        # Use LiveServerTestCase        

class SeleniumTests(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.selenium = webdriver.Firefox()
        super(SeleniumTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumTests, cls).tearDownClass()

    def test_add_speech(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/speech/add'))
        text_input = self.selenium.find_element_by_name('text')
        text_input.send_keys('This is a speech')
        self.selenium.find_element_by_xpath('//input[@value="Add speech"]').click()
        self.assertIn('/speech/1', self.selenium.current_url)

