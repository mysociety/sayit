from django.conf import settings
from django.utils import simplejson as json

from speeches.tests import InstanceTestCase
from speeches.models import Speech

class SpeechAPITests(InstanceTestCase):

    def setUp(self):
        super(SpeechAPITests, self).setUp()

        # create the public and private speeches
        self.public_speech = Speech.objects.create(title="Public", public=True, instance=self.instance)
        self.private_speech = Speech.objects.create(title="Private", public=False, instance=self.instance)


    def get_speech_from_api(self, speech):
        url = '/api/v0.1/speech/' + str(speech.id) + '/?format=json'
        # print "%s (%s): %s" % (speech, speech.id, url)
        return self.client.get(url)


    def test_speech_list(self):
        resp = self.client.get('/api/v0.1/speech/?format=json')
        data = json.loads(resp.content)
        objects = data['objects']

        self.assertEqual(len(objects), 1)

        self.assertEqual(objects[0]['title'], "Public")

    def test_public_speech_visible(self):
        resp = self.get_speech_from_api(self.public_speech)
        self.assertEqual(resp.status_code, 200)


    def test_private_speech_hidden(self):
        resp = self.get_speech_from_api(self.private_speech)
        self.assertEqual(resp.status_code, 404)
