from django.core.management import call_command
from haystack.query import SearchQuerySet
from instances.tests import InstanceTestCase

from speeches.models import Speech, Speaker, Section

class SearchTests(InstanceTestCase):
    def test_search(self):
        s1 = self.instance.speaker_set.create(name='Speaker 1')
        s2 = self.instance.speaker_set.create(name='Speaker 2')
        self.instance.speech_set.create(speaker=s1, text='Some text by speaker 1')
        self.instance.speech_set.create(speaker=s1, text='Some more text by speaker 1')
        self.instance.speech_set.create(speaker=s2, text='Some text by speaker 2')
        call_command('rebuild_index', verbosity=0, interactive=False)

        results = SearchQuerySet()
        self.assertEqual( results.count(), 3 )
        self.assertEqual( results.filter(speaker=s1.id).count(), 2 )
        self.assertEqual( results.filter(speaker=s2.id).count(), 1 )
        self.assertEqual( results.filter(instance=None).count(), 0 )
