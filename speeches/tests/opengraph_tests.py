from mock import patch, Mock

import django
from django.utils.six import assertRegex
from django.test.utils import override_settings
from django.utils import unittest

import opengraph

from speeches.tests import InstanceTestCase, OverrideMediaRootMixin
from speeches.models import Speaker, Speech, Section
from speeches import models

m = Mock()
m.return_value = ('speeches/fixtures/test_inputs/Ferdinand_Magellan.jpg', None)

skip_old_django = unittest.skipIf(
    django.VERSION[:2] == (1, 4),
    "Prior to Django 1.5, override_settings didn't sort out MEDIA_URL properly - see https://code.djangoproject.com/ticket/17744",
    )

@override_settings(MEDIA_URL='/uploads/')
@patch.object(models, 'urlretrieve', m)
class OpenGraphTests(OverrideMediaRootMixin, InstanceTestCase):
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
        self.steve_speech = Speech.objects.create(
            text="A Steve speech",
            instance=self.instance,
            speaker=self.steve,
            section=self.section,
            )

    def test_default_instance_homepage(self):
        resp = self.client.get('/')

        graph = opengraph.OpenGraph()
        graph.parser(resp.content)
        self.assertTrue(graph.is_valid())

    @skip_old_django
    def test_speaker_detail_page(self):
        resp = self.client.get('/speaker/%s' % self.steve.slug)

        graph = opengraph.OpenGraph()
        graph.parser(resp.content)
        assert graph.is_valid()
        assertRegex(self, graph.image, '/uploads/speakers/default/image.*.jpg')

    @skip_old_django
    def test_speech_detail_page(self):
        resp = self.client.get('/speech/%s' % self.steve_speech.id)

        graph = opengraph.OpenGraph()
        graph.parser(resp.content)
        self.assertTrue(graph.is_valid())
        assertRegex(self, graph.image, '/uploads/speakers/default/image.*.jpg')

    def test_section_detail_page(self):
        resp = self.client.get('/sections/%s' % self.section.id)

        graph = opengraph.OpenGraph()
        graph.parser(resp.content)
        self.assertTrue(graph.is_valid())
