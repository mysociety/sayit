import re
from mock import patch, Mock

import lxml.html

from django.utils.six import assertRegex
from django.utils.six.moves import urllib
from django.test.utils import override_settings

from speeches.tests import InstanceTestCase, OverrideMediaRootMixin
from speeches.models import Speaker, Speech, Section
from speeches import models

m = Mock()
m.return_value = ('speeches/fixtures/test_inputs/Ferdinand_Magellan.jpg', None)


@override_settings(MEDIA_URL='/uploads/')
class OpenGraphTests(OverrideMediaRootMixin, InstanceTestCase):
    @patch.object(models, 'urlretrieve', m)
    def setUp(self):
        super(OpenGraphTests, self).setUp()

        self.steve = Speaker.objects.create(
            name='Steve',
            instance=self.instance,
            image='http://example.com/image.jpg',
            )
        self.section = Section.objects.create(
            heading='Test section',
            instance=self.instance,
            )
        self.section_with_description = Section.objects.create(
            heading='Section with description',
            instance=self.instance,
            description='Section is described here',
            )
        self.section_with_html_description = Section.objects.create(
            heading='Bold Section',
            instance=self.instance,
            description='<b>Section is described <a href="/">here</a></b>',
            )
        self.steve_speech = Speech.objects.create(
            text="A Steve speech",
            instance=self.instance,
            speaker=self.steve,
            section=self.section,
            )
        self.speech_long_html_description = Speech.objects.create(
            text=(
                "<i>But I must explain to you how all this mistaken idea of "
                "denouncing pleasure and praising pain was born and I will "
                "give you a complete account of the system, and expound the "
                "actual teachings of the great explorer of the truth, the "
                "master-builder of human happiness.</i>"),
            instance=self.instance,
            speaker=self.steve,
            section=self.section,
            )

    def assert_opengraph_matches(self, response, graph):
        """Check that the response matches the graph.

        The graph should be passed in as a dictionary of opengraph
        property name to a content test. The test can be either
          * A string - this must be equal to the content of that key, or
          * A compliled regular expression - which must be found in the
            content for that OpenGraph key in a regex search.

        For example:
        {
            'title': 'OpenGraph title of the page',
            'url:': re.compile('http://testing.example.com:8000/images/*.jpg'),
        }

        Extra items in the graph in resp will be ignored - we're only
        checking that everything in graph appears correctly.
        """
        # Keys that should be URLs if they exist
        url_keys = set((
            'url', 'image', 'audio', 'video', 'image:url',
            'image:secure_url', 'video:secure_url', 'audio:secure_url'))

        parser = lxml.html.HTMLParser(encoding='utf-8')
        root = lxml.html.fromstring(response.content, parser=parser)

        for key, test in graph.items():
            content = root.xpath(".//meta[@property='og:%s']/@content" % key)
            self.assertEqual(len(content), 1)
            content = content[0]

            if hasattr(test, 'pattern'):
                assertRegex(self, content, test)
            else:
                self.assertEqual(content, test)

            if key in url_keys:
                # Check that the url is absolute.
                self.assertTrue(
                    urllib.parse.urlsplit(content).netloc,
                    'og:%s must be an absolute URL, not %s' % (key, content)
                    )

    def test_default_instance_homepage(self):
        self.assert_opengraph_matches(
            self.client.get('/'),
            {'title': 'SayIt',
             'url': 'http://testing.example.org:8000/',
             'site_name': 'SayIt',
             'description': 'Transcripts for the modern internet',
             'type': 'website',
             'image': 'http://testing.example.org:8000/static/speeches/img/apple-touch-icon-152x152.png',
             }
            )

    def test_speaker_detail_page(self):
        self.assert_opengraph_matches(
            self.client.get('/speaker/%s' % self.steve.slug),
            {'title': 'View Speaker: Steve :: SayIt',
             'url': 'http://testing.example.org:8000/speaker/%s' % self.steve.slug,
             'site_name': 'SayIt',
             'description': 'Speeches by Steve',
             'type': 'website',
             'image': re.compile('http://testing.example.org:8000/uploads/speakers/default/image.*.jpg'),
             }
            )

    def test_speech_detail_page(self):
        self.assert_opengraph_matches(
            self.client.get('/speech/%s' % self.steve_speech.id),
            {'title': u'\u201cA Steve speech\u201d :: SayIt',
             'url': 'http://testing.example.org:8000/speech/%s' % self.steve_speech.id,
             'site_name': 'SayIt',
             'description': 'A Steve speech',
             'type': 'website',
             'image': re.compile('http://testing.example.org:8000/uploads/speakers/default/image.*.jpg'),
             }
            )

        self.assert_opengraph_matches(
            self.client.get('/speech/%s' % self.speech_long_html_description.id),
            {'title': u'\u201cBut I must explain to you how ...\u201d :: SayIt',
             'url': 'http://testing.example.org:8000/speech/%s' % self.speech_long_html_description.id,
             'site_name': 'SayIt',
             'description': (
                 'But I must explain to you how all this mistaken idea of '
                 'denouncing pleasure and praising pain was born and I will '
                 'give you a complete account of the system, ...'),
             'type': 'website',
             'image': re.compile('http://testing.example.org:8000/uploads/speakers/default/image.*.jpg'),
             }
            )

    def test_section_detail_page(self):
        self.assert_opengraph_matches(
            self.client.get('/section/%s' % self.section.id),
            {'title': 'View Section: Test section :: SayIt',
             'url': 'http://testing.example.org:8000/section/%s' % self.section.id,
             'site_name': 'SayIt',
             'description': 'Transcripts for the modern internet',
             'type': 'website',
             'image': 'http://testing.example.org:8000/static/speeches/img/apple-touch-icon-152x152.png',
             }
            )

    def test_section_with_description_detail_page(self):
        self.assert_opengraph_matches(
            self.client.get('/section/%s' % self.section_with_description.id),
            {'title': 'View Section: Section with description :: SayIt',
             'url': 'http://testing.example.org:8000/section/%s' % self.section_with_description.id,
             'site_name': 'SayIt',
             'description': 'Section is described here',
             'type': 'website',
             'image': 'http://testing.example.org:8000/static/speeches/img/apple-touch-icon-152x152.png',
             }
            )

    def test_section_with_html_description_detail_page(self):
        self.assert_opengraph_matches(
            self.client.get('/section/%s' % self.section_with_html_description.id),
            {'title': 'View Section: Bold Section :: SayIt',
             'url': 'http://testing.example.org:8000/section/%s' % self.section_with_html_description.id,
             'site_name': 'SayIt',
             'description': 'Section is described here',
             'type': 'website',
             'image': 'http://testing.example.org:8000/static/speeches/img/apple-touch-icon-152x152.png',
             }
            )
