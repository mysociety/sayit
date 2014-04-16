from datetime import datetime, date, time, timedelta

from django.test import TestCase

from speeches.models import Section, Speech
from speeches.tests import create_sections
from instances.models import Instance
from speeches.tests import InstanceTestCase

class SectionModelTests(TestCase):

    def setUp(self):
        create_sections([
            { 'title': "Government Debates", 'subsections': [
                { 'title': "Monday 25th March", 'subsections': [
                    { 'title': "Oral Answers to Questions - Silly Walks",
                      'speeches': [ 4, date(2013, 3, 25), time(9, 0) ],
                    },
                    { 'title': "Bill on Silly Walks",
                      'speeches': [ 2, date(2013, 3, 25), time(12, 0) ],
                    },
                ] },
                { 'title': "Friday 29th March", 'subsections': [
                    { 'title': "Fixed Easter Bill", 'subsections': [
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
            { 'title': "Government Written Answers", 'subsections': [
                { 'title': "Ministry of Aardvarks", 'subsections': [
                    { 'title': "March",
                      'speeches': [ 3, None, None ],
                    },
                ] },
                { 'title': "Ministry of Silly Walks", 'subsections': [
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
        self.assertEqual(all_ministries, [ 'Aardvarks', 'Silly Walks', 'Something Else' ])

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

        speeches = Section.objects.get(title='Ministry of Silly Walks').children.get(title='Wednesday 6th of March').speech_set.all()
        p = Speech.objects.filter(section=Section.objects.get(title='March')).reverse()[0]
        q = Speech.objects.filter(section=Section.objects.get(title='Thursday 7th of March'))[0]
        self.assertEqual( speeches[0].get_previous_speech(), p )
        self.assertEqual( speeches[0].get_next_speech(), q )

    def test_section_descendant_speeches_queryset(self):
        top_level = Section.objects.get(title='Government Written Answers')

        # Get all speeches
        speeches = top_level.descendant_speeches()
        self.assertEqual(speeches.count(), 6)

        # Check that filtering works as expected
        test_date = date(2013, 3, 7)
        on_test_date = speeches.filter(start_date=test_date)
        self.assertEqual(on_test_date.count(), 2)

    def test_section_get_or_create_with_parents(self):

        instance, _ = Instance.objects.get_or_create(label='get-or-create-with-parents')

        # Test that not passing an instance leads to an exception
        self.assertRaises(Exception, Section.objects.get_or_create_with_parents, {"titles": ("Foo", "Bar", "Baz")} )

        # Create an initial set of sections
        baz_section = Section.objects.get_or_create_with_parents(instance=instance, titles=("Foo", "Bar", "Baz"))
        bar_section = baz_section.parent
        foo_section = bar_section.parent
        self.assertEqual(baz_section.title, "Baz")
        self.assertEqual(baz_section.instance, instance)
        self.assertEqual(foo_section.parent, None)
        self.assertEqual(foo_section.instance, instance)

        # Create the same ones again, check same child section returned
        baz_again_section = Section.objects.get_or_create_with_parents(instance=instance, titles=("Foo", "Bar", "Baz"))
        self.assertEqual(baz_again_section, baz_section)

        # Create a similar set and check only new ones created
        bundy_section = Section.objects.get_or_create_with_parents(instance=instance, titles=("Foo", "Bar", "Bundy"))
        self.assertEqual(bundy_section.title, "Bundy")
        self.assertEqual(bundy_section.parent, bar_section)


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
        self.assertRedirects(resp, '%s' % new_section.slug)
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
        self.assertRedirects(resp, '%s/%s' % (section.slug, new_section.slug))
        # Check in db
        subsection = Section.objects.get(id=new_section.id)
        self.assertEquals(subsection.title, 'A test subsection')
        self.assertEquals(subsection.parent, section)

    def test_section_page_lists_speeches(self):
        section = Section.objects.create(title='A test section', instance=self.instance)
        subsection = Section.objects.create(title='A test subsection', parent=section, instance=self.instance)

        # Assert no speeches
        resp = self.client.get('/sections/%d' % subsection.id)
        self.assertSequenceEqual([], list(resp.context['section_tree']))

        speech = Speech.objects.create(text="A test speech", section=subsection, instance=self.instance)
        resp = self.client.get('/sections/%d' % subsection.id)
        self.assertSequenceEqual([(speech, {'speech':True, 'new_level': True, 'closed_levels': [1]})], list(resp.context['section_tree']))

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

    def test_section_deletion(self):
        # Set up the section
        section = Section.objects.create(title='A test section', instance=self.instance)
        speech = Speech.objects.create(text="A test speech", section=section, instance=self.instance)
        resp = self.client.get('/sections/%d' % section.id)
        self.assertSequenceEqual([(speech, {'speech':True, 'new_level': True, 'closed_levels': [1]})], list(resp.context['section_tree']))

        # GET form (confirmation page)
        resp = self.client.get(section.get_delete_url())
        self.assertContains(resp, '<input type="submit" value="Confirm delete?"')

        section_db = Section.objects.get(id=section.id)
        self.assertEqual(section, section_db)

        speech_db = Speech.objects.get(id=speech.id)
        self.assertEqual(speech_db.section_id, section.id)

        # POST form (do the deletion)
        resp = self.client.post(section.get_delete_url())

        self.assertRedirects(resp, 'speeches')

        self.assertEqual(Section.objects.filter(id=section.id).count(), 0)

        speech_db = Speech.objects.get(id=speech.id)
        self.assertEqual(speech_db.section_id, None)

    def test_section_in_other_instance(self):
        other_instance = Instance.objects.create(label='other')
        section = Section.objects.create(title='A test section', instance=other_instance)
        self.assertEqual(section.slug, 'a-test-section')
        section = Section.objects.create(title='A test section', instance=self.instance)
        self.assertEqual(section.slug, 'a-test-section')
        section = Section.objects.create(title='A test section', instance=other_instance)
        self.assertEqual(section.slug, 'a-test-section-2')
        resp = self.client.get('/a-test-section-2')
        self.assertContains( resp, 'Not Found', status_code=404 )
