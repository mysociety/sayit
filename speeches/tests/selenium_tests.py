import os
import tempfile
import shutil

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from django.test.utils import override_settings
from django.utils import unittest
from django.conf import settings

import speeches
from speeches.models import Speaker, Speech
from speeches.tests import InstanceLiveServerTestCase

skip_selenium = not os.environ.get('SELENIUM_TESTS', False)

@unittest.skipIf(skip_selenium, 'Selenium tests not requested')
@override_settings(MEDIA_ROOT=tempfile.mkdtemp(), ATT_API_URL='http://att.api.url.example.org/')
class SeleniumTests(InstanceLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        if getattr(cls, "__unittest_skip__", False):
            return
        cls.selenium = webdriver.Firefox()
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')
        super(SeleniumTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "__unittest_skip__", False):
            return
        cls.selenium.quit()
        super(SeleniumTests, cls).tearDownClass()

    def tearDown(self):
        # Clear the speeches folder if it exists
        speeches_folder = os.path.join(settings.MEDIA_ROOT, 'speeches')
        if(os.path.exists(speeches_folder)):
            shutil.rmtree(speeches_folder)

    @property
    def live_server_url(self):
        url = super(SeleniumTests, self).live_server_url
        return url.replace('localhost', 'testing.127.0.0.1.xip.io')

    def test_select_text_and_audio(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/speech/add'))

        # Assert form is shown with audio input and text input
        self.assertTrue(self.selenium.find_element_by_id("speech-form").is_displayed())
        self.assertTrue(self.selenium.find_element_by_id("id_audio_controls").is_displayed())
        self.assertTrue(self.selenium.find_element_by_id("id_text_controls").is_displayed())

    def test_add_speech(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/speech/add'))
        text_input = self.selenium.find_element_by_name('text')
        text_input.send_keys('This is a speech')
        self.selenium.find_element_by_xpath('//input[@value="Add speech"]').click()
        speech = Speech.objects.order_by('-created')[0]
        self.assertIn('/speech/%d' % speech.id, self.selenium.current_url)

    def test_upload_audio(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/speech/add'))
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
        speech = Speech.objects.order_by('-created')[0]
        self.assertIn('/speech/%d' % speech.id, self.selenium.current_url)

    def test_speaker_autocomplete(self):
        # Put a person in the db for the autocomplete to find
        speaker = Speaker.objects.create(name='Name', instance=self.instance)

        # Type a name in and select it
        self.selenium.get('%s%s' % (self.live_server_url, '/speech/add'))
        speaker_input = self.selenium.find_element_by_xpath("//div[@id='s2id_id_speaker']/child::a").click()
        self.selenium.find_element_by_xpath('//div[@class="select2-result-label"]').click()
        # Check it is selected
        selection_element = self.selenium.find_element_by_xpath('//div[@id="s2id_id_speaker"]/descendant::span')
        self.assertIn('Name', selection_element.text)
        speaker_input = self.selenium.find_element_by_id("id_speaker")
        self.assertTrue(speaker_input.get_attribute('value') == str(speaker.id))
        # Check we can unselect it
        self.selenium.find_element_by_xpath('//div[@id="s2id_id_speaker"]/descendant::abbr[@class="select2-search-choice-close"]').click()
        speaker_input = self.selenium.find_element_by_id("id_speaker")
        self.assertTrue(speaker_input.get_attribute('value') == "")
