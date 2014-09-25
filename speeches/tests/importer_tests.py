import datetime
from mock import patch, Mock

from speeches.tests import InstanceTestCase
from speeches.importers.import_akomantoso import ImportAkomaNtoso
from speeches.models import Speech, Speaker, Section
from speeches.importers import import_akomantoso

m = Mock()
m.return_value = open('speeches/fixtures/test_inputs/Debate_Bungeni_1995-10-31.xml', 'rb')

@patch.object(import_akomantoso, 'urlopen', m)
class AkomaNtosoImportTestCase(InstanceTestCase):
    def setUp(self):
        super(AkomaNtosoImportTestCase, self).setUp()
        self.importer = ImportAkomaNtoso(instance=self.instance, commit=True)

    def test_import_sample_file(self):
        self.importer.import_document(
            'speeches/fixtures/test_inputs/Debate_Bungeni_1995-10-31.xml')

        # To get us started, let's just check that we get the right kind of
        # speech in the right order.
        self.assertEqual(
            [x.type for x in Speech.objects.all()],
            [u'scene', u'other', u'narrative', u'speech', u'question',
             u'summary', u'speech', u'answer', u'narrative', u'speech',
             u'narrative']
            )

    def test_import_remote_file(self):
        self.importer.import_document(
            'http://examples.akomantoso.org/php/download.php?file=Debate_Bungeni_1995-10-31.xml')

        # To get us started, let's just check that we get the right kind of
        # speech in the right order.
        self.assertEqual(
            [x.type for x in Speech.objects.all()],
            [u'scene', u'other', u'narrative', u'speech', u'question',
             u'summary', u'speech', u'answer', u'narrative', u'speech',
             u'narrative']
            )

    def test_xpath_preface_elements(self):
        self.importer.import_document(
            'speeches/fixtures/test_inputs/test_xpath.xml')
        self.assertEqual(
            [ x.title for x in Section.objects.all() ],
            [ 'This is the title' ]
        )
        self.assertEqual(
            [ x.start_date for x in Speech.objects.all() ],
            [ datetime.date(2014, 7, 24) ]
        )

    def test_unicode_character(self):
        self.importer.import_document(
            'speeches/fixtures/test_inputs/test_unicode_character.xml')

        self.assertEqual(
            [ x.type for x in Speech.objects.all() ],
            [ 'other' ]
            )

    def test_blank_speakers(self):
        self.importer.import_document(
            'speeches/fixtures/test_inputs/test_blank_speakers.xml')

        speaker = Speaker.objects.get(name='Speaker')
        speeches = Speech.objects.all()
        speeches_s = Speech.objects.filter(type='speech')
        self.assertEqual(speeches.count(), speeches_s.count())

        for i in range(4):
            s = speaker if i%2 else None
            sd = 'Speaker' if i>1 else None
            self.assertEqual(speeches[i].speaker, s)
            self.assertEqual(speeches[i].speaker_display, sd)
