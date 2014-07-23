import lxml.etree as etree
from speeches.external.formencode import xml_compare

from speeches.tests import InstanceTestCase
from speeches.models import Speech, Section, Speaker


class AkomaNtosoOutputTestCase(InstanceTestCase):
    def test_output_speech(self):
        speaker = Speaker.objects.create(
            instance=self.instance,
            name='Test Speaker',
            )
        section = Section.objects.create(
            instance=self.instance,
            title='Test Section')
        Speech.objects.create(
            instance=self.instance,
            text='Test Speech',
            speaker=speaker,
            type='speech',
            section=section,
            )

        resp = self.client.get('/test-section.an')
        output = resp.content
        lxml1 = etree.fromstring(output)

        expected = """
            <akomaNtoso>
              <debate>
                <meta>
                  <references>
                    <TLCPerson href="/ontology/person/testserver/test-speaker"
                               id="test-speaker" showAs="Test Speaker"/>
                  </references>
                </meta>
                <debateBody>
                  <debateSection>
                    <heading>Test Section</heading>
                    <speech by="#test-speaker">
                      <from>Test Speaker</from>
                      Test Speech
                    </speech>
                  </debateSection>
                </debateBody>
              </debate>
            </akomaNtoso>
            """
        lxml2 = etree.fromstring(expected)

        assert xml_compare(lxml1, lxml2)
