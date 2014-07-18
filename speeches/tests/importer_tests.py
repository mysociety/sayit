from speeches.tests import InstanceTestCase
from speeches.importers.import_akomantoso import ImportAkomaNtoso
from speeches.models import Speech


class AkomaNtosoImportTestCase(InstanceTestCase):
    def test_import_sample_file(self):
        importer = ImportAkomaNtoso(instance=self.instance, commit=True)
        importer.import_document(
            'speeches/fixtures/test_inputs/Debate_Bungeni_1995-10-31.xml')

        # To get us started, let's just check that we get the right kind of
        # speech in the right order.
        self.assertEqual(
            [x.type for x in Speech.objects.all()],
            [u'scene', u'other', u'narrative', u'speech', u'question',
             u'summary', u'speech', u'answer', u'narrative', u'speech']
            )
