# -*- coding: utf-8 -*-

from speeches.tests import InstanceTestCase
from speeches.models import Speaker, Section

class SlugTests(InstanceTestCase):

    def test_all_latin_speaker_slug(self):
        latin_speaker = Speaker.objects.create(
            name='Foo Bar',
            instance=self.instance
        )
        try:
            self.assertEqual(
                latin_speaker.slug,
                'foo-bar'
            )
        finally:
            latin_speaker.delete()

    def test_all_cjk_speaker_slug(self):
        cjk_speaker = Speaker.objects.create(
            name=u'張家祝',
            instance=self.instance
        )
        cjk_speaker_duplicate = Speaker.objects.create(
            name=u'張家祝',
            instance=self.instance
        )
        try:
            self.assertEqual(
                cjk_speaker.slug,
                u'張家祝',
            )
            self.assertEqual(
                cjk_speaker_duplicate.slug,
                u'張家祝-2',
            )
        finally:
            cjk_speaker.delete()
            cjk_speaker_duplicate.delete()

    def test_cyrillic_speaker_slug(self):
        cyrillic_speaker = Speaker.objects.create(
            name=u'Борщ со сметаной',
            instance=self.instance
        )
        try:
            self.assertEqual(
                cyrillic_speaker.slug,
                u'борщ-со-сметаной',
            )
        finally:
            cyrillic_speaker.delete()

    def test_all_cjk_section_slug(self):
        cjk_section = Section.objects.create(
            heading=u'經貿國是會議全國大會總結',
            instance=self.instance
        )
        try:
            self.assertEqual(
                cjk_section.slug,
                u'經貿國是會議全國大會總結',
            )
        finally:
            cjk_section.delete()
