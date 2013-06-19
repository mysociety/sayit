from datetime import datetime, date, time, timedelta

from django.test import TestCase

from speeches.models import Section, Speech
from instances.models import Instance
from instances.tests import InstanceTestCase

class SectionModelTests(TestCase):

    def create_sections(self, node, parent=None):
        if parent:
            instance = parent.instance
        else:
            instance, _ = Instance.objects.get_or_create(label='whatever')

        for item in node:
            s = Section.objects.create( instance=instance, title=item['title'], parent=parent )
            if 'items' in item:
                self.create_sections(item['items'], s)
            if 'speeches' in item:
                num, d, t = item['speeches']
                for i in range(0, num):
                    Speech.objects.create(
                        instance = instance,
                        section = s,
                        text = 'rhubarb rhubarb',
                        start_date = d,
                        start_time = t,
                    )
                    if t:
                        t = (datetime.combine(date.today(), t) + timedelta(minutes=10)).time()

    def setUp(self):
        self.create_sections([
            { 'title': "Government Debates", 'items': [
                { 'title': "Monday 25th March", 'items': [
                    { 'title': "Oral Answers to Questions - Silly Walks",
                      'speeches': [ 4, date(2013, 3, 25), time(9, 0) ],
                    },
                    { 'title': "Bill on Silly Walks",
                      'speeches': [ 2, date(2013, 3, 25), time(12, 0) ],
                    },
                ] },
                { 'title': "Friday 29th March", 'items': [
                    { 'title': "Fixed Easter Bill", 'items': [
                        { 'title': "Z Clause",
                          'speeches': [ 2, date(2013, 3, 29), time(15, 00) ],
                        },
                        { 'title': "Clause 1",
                          'speeches': [ 3, date(2013, 3, 29), time(14, 30) ],
                        },
                        { 'title': "New Clause 1",
                          'speeches': [ 3, date(2013, 3, 29), time(14, 0) ],
                        },
                    ] },
                ] },
            ] },
            { 'title': "Government Written Answers", 'items': [
                { 'title': "Ministry of Aardvarks", 'items': [
                    { 'title': "March",
                      'speeches': [ 3, None, None ],
                    },
                ] },
                { 'title': "Ministry of Silly Walks", 'items': [
                    { 'title': "Wednesday 6th of March",
                      'speeches': [ 1, date(2013, 3, 6), None ],
                    },
                    { 'title': "Thursday 7th of March",
                      'speeches': [ 2, date(2013, 3, 7), None ],
                    },
                ] },
                { 'title': "Ministry of Something Else"
                },
            ] },
        ])

    def test_datetimes(self):
        section = Section.objects.get(title="Bill on Silly Walks")
        dts = sorted(section.speech_datetimes())
        self.assertEqual(dts[0], datetime(2013, 3, 25, 12, 0))
        self.assertEqual(dts[1], datetime(2013, 3, 25, 12, 10))

    def test_section_creation(self):

        # Get the top level section:
        top_level = Section.objects.get(title='Government Written Answers')

        all_sections = top_level.get_descendants

        self.assertEqual(len(list(all_sections)),
                         6,
                         "The total number of sections was wrong")

        all_ministries = top_level.get_children

        self.assertEqual(len(all_ministries),
                         3,
                         "The number of ministries was wrong")

        # Check that the sections are in insertion order:
        all_ministries = [ a.title.replace('Ministry of ', '') for a in all_ministries ]
        self.assertEqual(all_ministries, [ 'Silly Walks', 'Aardvarks', 'Something Else' ])

        # Get all speeches under a section, where everything should be
        # sorted by speech date:
        top_level = Section.objects.get(title="Government Debates")
        children = top_level.get_descendants
        children = [ c.title for c in children ]
        self.assertEqual(children, [ 'Monday 25th March', 'Oral Answers to Questions - Silly Walks', 'Bill on Silly Walks', 'Friday 29th March', 'Fixed Easter Bill', 'New Clause 1', 'Clause 1', 'Z Clause' ])

    def test_section_next_previous(self):
        top_level = Section.objects.get(title='Government Written Answers')
        depts = top_level.get_children
        self.assertEqual( depts[0].get_previous_node(), None )
        self.assertEqual( depts[1].get_previous_node(), depts[0] )
        self.assertEqual( depts[2].get_previous_node(), depts[1] )
        self.assertEqual( depts[0].get_next_node(), depts[1] )
        self.assertEqual( depts[1].get_next_node(), depts[2] )
        self.assertEqual( depts[2].get_next_node(), None )

        day = Section.objects.get(title='Monday 25th March')
        e = Section.objects.get(title='Fixed Easter Bill')
        debs = day.get_children
        self.assertEqual( debs[0].get_previous_node(), None )
        self.assertEqual( debs[1].get_previous_node(), debs[0] )
        self.assertEqual( debs[0].get_next_node(), debs[1] )
        self.assertEqual( debs[1].get_next_node(), e )

    def test_section_speech_next_previous(self):
        first_next = Section.objects.get(title='Bill on Silly Walks').speech_set.all()[0]
        speeches = Section.objects.get(title='Oral Answers to Questions - Silly Walks').speech_set.all()
        self.assertEqual( speeches[0].get_previous_speech(), None )
        self.assertEqual( speeches[0].get_next_speech(), speeches[1] )
        self.assertEqual( speeches[1].get_next_speech(), speeches[2] )
        self.assertEqual( speeches[2].get_next_speech(), speeches[3] )
        self.assertEqual( speeches[3].get_next_speech(), first_next )

        speeches = Section.objects.get(title='Ministry of Aardvarks').children.get(title='March').speech_set.all()
        p = Speech.objects.filter(section=Section.objects.get(title='Thursday 7th of March')).reverse()[0]
        self.assertEqual( speeches[0].get_previous_speech(), p )
        self.assertEqual( speeches[0].get_next_speech(), speeches[1] )
        self.assertEqual( speeches[1].get_next_speech(), speeches[2] )
        self.assertEqual( speeches[2].get_next_speech(), None )

class SectionSiteTests(InstanceTestCase):
    """Tests for the section functionality"""

    def test_add_section_fails_on_empty_form(self):
        resp = self.client.post('/sections/add')
        self.assertFormError(resp, 'form', 'title', 'This field is required.')

    def test_add_section_with_title(self):
        resp = self.client.post('/sections/add', {
            'title': 'A test section'
        })
        new_section = Section.objects.order_by('-id')[0]
        self.assertRedirects(resp, 'sections/%d' % new_section.id)
        # Check in db
        section = Section.objects.get(id=new_section.id)
        self.assertEquals(section.title, 'A test section')

    def test_add_section_in_section(self):
        section = Section.objects.create(title='Test section', instance=self.instance)
        resp = self.client.post('/sections/add', {
            'parent': section.id,
            'title': 'A test subsection'
        })
        new_section = Section.objects.order_by('-id')[0]
        self.assertRedirects(resp, 'sections/%d' % new_section.id)
        # Check in db
        subsection = Section.objects.get(id=new_section.id)
        self.assertEquals(subsection.title, 'A test subsection')
        self.assertEquals(subsection.parent, section)

    def test_section_page_lists_speeches(self):
        section = Section.objects.create(title='A test section', instance=self.instance)
        subsection = Section.objects.create(title='A test subsection', parent=section, instance=self.instance)

        # Assert no speeches
        resp = self.client.get('/sections/%d' % subsection.id)
        self.assertSequenceEqual([], resp.context['speech_list'])

        speech = Speech.objects.create(text="A test speech", section=subsection, instance=self.instance)
        resp = self.client.get('/sections/%d' % subsection.id)
        self.assertSequenceEqual([speech], resp.context['speech_list'])

    def test_section_page_lists_subsections(self):
        section = Section.objects.create(title='A test section', instance=self.instance)

        # Assert no subsections
        resp = self.client.get('/sections/%d' % section.id)
        self.assertSequenceEqual([], resp.context['section'].get_descendants)

        subsection = Section.objects.create(title="A test subsection", parent=section, instance=self.instance)
        resp = self.client.get('/sections/%d' % section.id)
        self.assertSequenceEqual([subsection], resp.context['section'].get_descendants)

    def test_section_page_has_buttons_to_edit(self):
        # Add a section
        section = Section.objects.create(title='A test section', instance=self.instance)

        # Call the section's page
        resp = self.client.get('/sections/%d' % section.id)

        self.assertContains(resp, '<a href="/speech/add?section=%d">Add a new speech</a>' % section.id, html=True)
        self.assertContains(resp, '<a href="/sections/add?section=%d">Add a new subsection</a>' % section.id, html=True)

        self.assertContains(resp, '<a href="/sections/%d/edit">Edit section</a>' % section.id, html=True)
        self.assertContains(resp, '<a href="/sections/%d/delete">Delete section</a>' % section.id, html=True)

