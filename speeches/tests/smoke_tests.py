from instances.tests import InstanceTestCase

from speeches.models import Speech, Speaker, Section

class SmokeTests(InstanceTestCase):
    """Simple smoke tests (is it up?) of all the urls on the site"""

    def test_home_page(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_all_speakers_page(self):
        resp = self.client.get('/speeches')
        self.assertEqual(resp.status_code, 200)

    def test_a_speaker_page(self):
        # Add a speaker first
        speaker = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/abcd', name='Steve', instance=self.instance)
        resp = self.client.get('/speaker/%s' % speaker.id)
        self.assertEqual(resp.status_code, 200)

    def test_a_speech_page(self):
        # Add a speech first
        speech = Speech.objects.create(text='Testing speech page', instance=self.instance)
        resp = self.client.get('/speech/%s' % speech.id)
        self.assertEqual(resp.status_code, 200)

    def test_add_speech_page(self):
        resp = self.client.get('/speech/add')
        self.assertEqual(resp.status_code, 200)

    def test_a_section_page(self):
        # Add a section first
        section = Section.objects.create(title="A Section", instance=self.instance)
        resp = self.client.get("/section/%s" % section.id)
        self.assertEqual(resp.status_code, 200)

    def test_add_section_page(self):
        resp = self.client.get("/section/add")
        self.assertEqual(resp.status_code, 200)

    def test_section_list_page(self):
        resp = self.client.get("/sections")
        self.assertEqual(resp.status_code, 200)
