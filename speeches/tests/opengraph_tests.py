import opengraph

from speeches.tests import InstanceTestCase

class OpenGraphTests(InstanceTestCase):
    def test_default_instance_homepage(self):
        resp = self.client.get('/')

        graph = opengraph.OpenGraph()
        graph.parser(resp.content)
        self.assertTrue(graph.is_valid())
