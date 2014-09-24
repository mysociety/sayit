import opengraph

from speeches.tests import InstanceTestCase
from speeches.models import Speaker, Speech, Section

class OpenGraphTests(InstanceTestCase):
    def setUp(self):
        super(OpenGraphTests, self).setUp()

        self.steve = Speaker.objects.create(
            name='Steve',
            instance=self.instance,
            image='http://example.com/image.jpg',
            )
        self.steve_speech = Speech.objects.create(
            text="A Steve speech",
            instance=self.instance,
            speaker=self.steve,
            )

    def test_default_instance_homepage(self):
        resp = self.client.get('/')

        graph = opengraph.OpenGraph()
        graph.parser(resp.content)
        self.assertTrue(graph.is_valid())

    def test_speaker_detail_page(self):
        resp = self.client.get('/speaker/%s' % self.steve.slug)

        graph = opengraph.OpenGraph()
        graph.parser(resp.content)
        assert graph.is_valid()

    def test_speech_detail_page(self):
        resp = self.client.get('/speech/%s' % self.steve_speech.id)

        graph = opengraph.OpenGraph()
        graph.parser(resp.content)
        self.assertTrue(graph.is_valid())
