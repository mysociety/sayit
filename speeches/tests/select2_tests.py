from six.moves.urllib.parse import urlencode
import json

from django_select2.util import register_field

from instances.models import Instance

from speeches.tests import InstanceTestCase

from speeches.models import Speaker, Section
from speeches.forms import SpeakerField, SectionField


class AjaxTests(InstanceTestCase):
    def setUp(self, *args, **kwargs):
        super(AjaxTests, self).setUp(*args, **kwargs)

        Speaker.objects.create(name='Alice', instance=self.instance)
        Speaker.objects.create(name='Alastair', instance=self.instance)
        Speaker.objects.create(name='Bob', instance=self.instance)

        Section.objects.create(title='Section A', instance=self.instance)
        Section.objects.create(title='Section B', instance=self.instance)
        Section.objects.create(title='Not This', instance=self.instance)

        other_instance = Instance.objects.create(label='other')
        Speaker.objects.create(name='Alan', instance=other_instance)
        Section.objects.create(title='Other', instance=other_instance)

    def test_lookup_speaker(self):
        # Copy what happens in AutoViewFieldMixin's __init__
        # in order to get the required field_id.
        field_id = register_field('speeches.forms.SpeakerField', SpeakerField())

        # The ajax queries look something like this:
        # /select2/fields/auto.json?term=al&page=1&context=&field_id=f5af12d0dbb3800ea6b8d88b4720ad7b625f1ae4&_=1399984568706
        data = urlencode({
            'term': 'al',
            'field_id': field_id,
            'page': 1,
            'context': '',
            })
        resp = self.client.get('/select2/fields/auto.json?' + data)

        results = json.loads(resp.content.decode())['results']

        # We should see Alice and Alastair, but not Bob (doesn't match),
        # or Alan (wrong instance).
        self.assertEqual(
            set([x['text'] for x in results]),
            set((u'Alice', u'Alastair'))
            )

    def test_lookup_section(self):
        field_id = register_field('speeches.forms.SectionField', SectionField())
        data = urlencode({
            'term': 'se',
            'field_id': field_id,
            'page': 1,
            'context': '',
        })
        resp = self.client.get('/select2/fields/auto.json?' + data)

        results = json.loads(resp.content.decode())['results']

        # We should see Sections, but not Not This (doesn't match),
        # or Other (wrong instance).
        self.assertEqual(
            set([x['text'] for x in results]),
            set((u'Section A', u'Section B'))
        )
