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
                      Test Speech
                    </speech>
                  </debateSection>
                </debateBody>
              </debate>
            </akomaNtoso>
            """
        lxml2 = etree.fromstring(expected)

        assert xml_compare(lxml1, lxml2)

    def test_output_scene(self):
        section = Section.objects.create(
            instance=self.instance,
            title='Test Section')
        Speech.objects.create(
            instance=self.instance,
            text='Test Scene',
            type='scene',
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
                  </references>
                </meta>
                <debateBody>
                  <debateSection>
                    <heading>Test Section</heading>
                    <scene>
                      Test Scene
                    </scene>
                  </debateSection>
                </debateBody>
              </debate>
            </akomaNtoso>
            """
        lxml2 = etree.fromstring(expected)

        assert xml_compare(lxml1, lxml2)

    def test_random_speech_type_renders_as_other(self):
        section = Section.objects.create(
            instance=self.instance,
            title='Test Section')
        Speech.objects.create(
            instance=self.instance,
            text='Text here',
            type='random',
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
                  </references>
                </meta>
                <debateBody>
                  <debateSection>
                    <heading>Test Section</heading>
                    <other>
                      Text here
                    </other>
                  </debateSection>
                </debateBody>
              </debate>
            </akomaNtoso>
            """
        lxml2 = etree.fromstring(expected)

        assert xml_compare(lxml1, lxml2)
