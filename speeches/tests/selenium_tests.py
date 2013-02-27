import os
import tempfile
import shutil

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from django.test import LiveServerTestCase
from django.test.utils import override_settings
from django.conf import settings

import speeches
from speeches.models import Speaker, Speech

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class SeleniumTests(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.selenium = webdriver.Firefox()
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')
        super(SeleniumTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumTests, cls).tearDownClass()

    def tearDown(self):
        # Clear the speeches folder if it exists
        speeches_folder = os.path.join(settings.MEDIA_ROOT, 'speeches')
        if(os.path.exists(speeches_folder)):
            shutil.rmtree(speeches_folder)

    def test_select_text_only(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/speech/add'))

        # Assert question is shown and form is hidden
        self.assertTrue(self.selenium.find_element_by_id("question").is_displayed())
        self.assertFalse(self.selenium.find_element_by_id("speech-form").is_displayed())

        # Select text
        self.selenium.find_element_by_id("text-link").click()

        # Assert form is show with text input
        self.assertTrue(self.selenium.find_element_by_id("speech-form").is_displayed())
        self.assertTrue(self.selenium.find_element_by_id("id_text_controls").is_displayed())

        # Assert audio and question are hidden
        self.assertFalse(self.selenium.find_element_by_id("id_audio_controls").is_displayed())
        self.assertFalse(self.selenium.find_element_by_id("question").is_displayed())

    def test_select_audio_only(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/speech/add'))

        # Assert question is shown and form is hidden
        self.assertTrue(self.selenium.find_element_by_id("question").is_displayed())
        self.assertFalse(self.selenium.find_element_by_id("speech-form").is_displayed())

        # Select audio
        self.selenium.find_element_by_id("audio-link").click()

        # Assert form is shown with audio input
        self.assertTrue(self.selenium.find_element_by_id("speech-form").is_displayed())
        self.assertTrue(self.selenium.find_element_by_id("id_audio_controls").is_displayed())

        # Assert text and question are hidden
        self.assertFalse(self.selenium.find_element_by_id("id_text_controls").is_displayed())
        self.assertFalse(self.selenium.find_element_by_id("question").is_displayed())

    def test_select_text_and_audio(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/speech/add'))

        # Assert question is shown and form is hidden
        self.assertTrue(self.selenium.find_element_by_id("question").is_displayed())
        self.assertFalse(self.selenium.find_element_by_id("speech-form").is_displayed())

        # Select both
        self.selenium.find_element_by_id("both-link").click()

        # Assert form is shown with audio input and text input
        self.assertTrue(self.selenium.find_element_by_id("speech-form").is_displayed())
        self.assertTrue(self.selenium.find_element_by_id("id_audio_controls").is_displayed())
        self.assertTrue(self.selenium.find_element_by_id("id_text_controls").is_displayed())

        # Assert Question is hidden
        self.assertFalse(self.selenium.find_element_by_id("question").is_displayed())

    def test_add_speech(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/speech/add'))
        self.selenium.find_element_by_id("text-link").click()
        text_input = self.selenium.find_element_by_name('text')
        text_input.send_keys('This is a speech')
        self.selenium.find_element_by_xpath('//input[@value="Add speech"]').click()
        self.assertIn('/speech/1', self.selenium.current_url)

    def test_upload_audio(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/speech/add'))
        self.selenium.find_element_by_id("audio-link").click()
        audio_file_input = self.selenium.find_element_by_name("audio")
        
        # The file input is covered by the button. This javascript takes the
        # input and moves it out so that when selenium tries to click on it (to
        # focus it for the send_keys) the click does not 'fall' on another
        # element.
        self.selenium.execute_script("""
            var $audio = $('input[name=audio]');
            $audio.insertAfter( $audio.parent() );
        """);
        
        audio_file_input.send_keys(os.path.join(self._in_fixtures, 'lamb.mp3'))
        self.selenium.find_element_by_xpath('//input[@value="Add speech"]').click()
        self.assertIn('/speech/1', self.selenium.current_url)

    def test_speaker_autocomplete(self):
        # Put a person in the db for the autocomplete to find
        speaker = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/abcde', name='Name')

        # Type a name in and select it
        self.selenium.get('%s%s' % (self.live_server_url, '/speech/add'))
        self.selenium.find_element_by_id("text-link").click()
        speaker_input = self.selenium.find_element_by_name("speaker-autocomplete")
        speaker_input.send_keys("Na")
        self.selenium.find_element_by_xpath('//div[@id="id-id_speaker_text"]/descendant::span').click()
        # Check it is selected
        selection_element = self.selenium.find_element_by_xpath('//span[@id="id_speaker-deck"]/child::span')
        self.assertIn('Name', selection_element.text)
        # Check we can unselect it
        self.selenium.find_element_by_xpath('//span[@id="id_speaker-deck"]/descendant::span[@class="remove div"]').click()
        speaker_input = self.selenium.find_element_by_name("speaker-autocomplete")
        self.assertTrue(speaker_input.get_attribute('value') == "")