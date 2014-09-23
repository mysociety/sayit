import opengraph

from speeches.tests import InstanceTestCase
from speeches.models import Speaker, Speech, Section

class OpenGraphTests(InstanceTestCase):
    def test_default_instance_homepage(self):
        resp = self.client.get('/')

        graph = opengraph.OpenGraph()
        graph.parser(resp.content)
        self.assertTrue(graph.is_valid())

    def test_speaker_detail_page(self):
        speaker = Speaker.objects.create(name='Steve', instance=self.instance, image='http://example.com/image.jpg')
        resp = self.client.get('/speaker/%s' % speaker.slug)

        graph = opengraph.OpenGraph()
        graph.parser(resp.content)
        self.assertTrue(graph.is_valid())
