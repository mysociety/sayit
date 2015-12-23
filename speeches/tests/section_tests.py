import re
from datetime import datetime, date, time

from django.test import TestCase

from speeches.models import Section, Speech
from speeches.tests import create_sections
from instances.models import Instance
from speeches.tests import InstanceTestCase


class SectionModelTests(TestCase):

    def setUp(self):
        create_sections([
            {'heading': "Government Debates", 'subsections': [
                {'heading': "Monday 25th March", 'subsections': [
                    {'heading': "Oral Answers to Questions - Silly Walks",
                     'speeches': [4, date(2013, 3, 25), time(9, 0)],
                     },
                    {'heading': "Bill on Silly Walks",
                     'speeches': [2, date(2013, 3, 25), time(12, 0)],
                     },
                ]},
                {'heading': "Friday 29th March", 'subsections': [
                    {'heading': "Fixed Easter Bill", 'subsections': [
                        {'heading': "Z Clause",
                         'speeches': [2, date(2013, 3, 29), time(15, 00)],
                         },
                        {'heading': "Clause 1",
                         'speeches': [3, date(2013, 3, 29), time(14, 30)],
                         },
                        {'heading': "New Clause 1",
                         'speeches': [3, date(2013, 3, 29), time(14, 0)],
                         },
                    ]},
                ]},
            ]},
            {'heading': "Government Written Answers", 'subsections': [
                {'heading': "Ministry of Aardvarks", 'subsections': [
                    {'heading': "March",
                     'speeches': [3, None, None],
                     },
                ]},
                {'heading': "Ministry of Silly Walks", 'subsections': [
                    {'heading': "Wednesday 6th of March",
                     'speeches': [1, date(2013, 3, 6), None],
                     },
                    {'heading': "Thursday 7th of March",
                     'speeches': [2, date(2013, 3, 7), None],
                     },
                ]},
                {'heading': "Ministry of Something Else"
                 },
            ]},
        ])

    def test_datetimes(self):
        section = Section.objects.get(heading="Bill on Silly Walks")
        dts = sorted(section.speech_datetimes())
        self.assertEqual(dts[0], datetime(2013, 3, 25, 12, 0))
        self.assertEqual(dts[1], datetime(2013, 3, 25, 12, 10))

    def test_section_creation(self):

        # Get the top level section:
        top_level = Section.objects.get(heading='Government Written Answers')

        all_sections = top_level.get_descendants

        self.assertEqual(len(list(all_sections)),
                         6,
                         "The total number of sections was wrong")

        all_ministries = top_level.get_children

        self.assertEqual(len(all_ministries),
                         3,
                         "The number of ministries was wrong")

        # Check that the sections are in insertion order:
        all_ministries = [a.heading.replace('Ministry of ', '') for a in all_ministries]
        self.assertEqual(all_ministries, ['Aardvarks', 'Silly Walks', 'Something Else'])

        # Get all speeches under a section, where everything should be
        # sorted by speech date:
        top_level = Section.objects.get(heading="Government Debates")
        children = top_level.get_descendants
        children = [c.heading for c in children]
        self.assertEqual(children, [
            'Monday 25th March', 'Oral Answers to Questions - Silly Walks', 'Bill on Silly Walks',
            'Friday 29th March', 'Fixed Easter Bill', 'New Clause 1', 'Clause 1', 'Z Clause'])

    def test_section_next_previous(self):
        top_level = Section.objects.get(heading='Government Written Answers')
        depts = top_level.get_children
        self.assertEqual(depts[0].get_previous_node(), None)
        self.assertEqual(depts[1].get_previous_node(), depts[0])
        self.assertEqual(depts[2].get_previous_node(), depts[1])
        self.assertEqual(depts[0].get_next_node(), depts[1])
        self.assertEqual(depts[1].get_next_node(), depts[2])
        self.assertEqual(depts[2].get_next_node(), None)

        day = Section.objects.get(heading='Monday 25th March')
        e = Section.objects.get(heading='Fixed Easter Bill')
        debs = day.get_children
        self.assertEqual(debs[0].get_previous_node(), None)
        self.assertEqual(debs[1].get_previous_node(), debs[0])
        self.assertEqual(debs[0].get_next_node(), debs[1])
        self.assertEqual(debs[1].get_next_node(), e)

    def test_section_speech_next_previous(self):
        first_next = Section.objects.get(heading='Bill on Silly Walks').speech_set.all()[0]
        speeches = Section.objects.get(heading='Oral Answers to Questions - Silly Walks').speech_set.all()
        self.assertEqual(speeches[0].get_previous_speech(), None)
        self.assertEqual(speeches[0].get_next_speech(), speeches[1])
        self.assertEqual(speeches[1].get_next_speech(), speeches[2])
        self.assertEqual(speeches[2].get_next_speech(), speeches[3])
        self.assertEqual(speeches[3].get_next_speech(), first_next)

        speeches = Section.objects.get(heading='Ministry of Silly Walks') \
            .children.get(heading='Wednesday 6th of March').speech_set.all()
        p = Speech.objects.filter(section=Section.objects.get(heading='March')).reverse()[0]
        q = Speech.objects.filter(section=Section.objects.get(heading='Thursday 7th of March'))[0]
        self.assertEqual(speeches[0].get_previous_speech(), p)
        self.assertEqual(speeches[0].get_next_speech(), q)

    def test_section_descendant_speeches_queryset(self):
        top_level = Section.objects.get(heading='Government Written Answers')

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
        self.assertRaises(Exception, Section.objects.get_or_create_with_parents, {"headings": ("Foo", "Bar", "Baz")})

        # Create an initial set of sections
        baz_section = Section.objects.get_or_create_with_parents(instance=instance, headings=("Foo", "Bar", "Baz"))
        bar_section = baz_section.parent
        foo_section = bar_section.parent
        self.assertEqual(baz_section.heading, "Baz")
        self.assertEqual(baz_section.instance, instance)
        self.assertEqual(foo_section.parent, None)
        self.assertEqual(foo_section.instance, instance)

        # Create the same ones again, check same child section returned
        baz_again_section = Section.objects.get_or_create_with_parents(
            instance=instance, headings=("Foo", "Bar", "Baz"))
        self.assertEqual(baz_again_section, baz_section)

        # Create a similar set and check only new ones created
        bundy_section = Section.objects.get_or_create_with_parents(instance=instance, headings=("Foo", "Bar", "Bundy"))
        self.assertEqual(bundy_section.heading, "Bundy")
        self.assertEqual(bundy_section.parent, bar_section)


class SectionSiteTests(InstanceTestCase):
    """Tests for the section functionality"""

    def test_add_section_fails_on_empty_form(self):
        resp = self.client.post('/section/add')
        self.assertFormError(resp, 'form', None, 'You must specify at least one of num/heading/subheading')

    def test_add_section_with_heading(self):
        resp = self.client.post('/section/add', {
            'heading': 'A test section'
        })
        new_section = Section.objects.order_by('-id')[0]
        self.assertRedirects(resp, '/%s' % new_section.slug)
        # Check in db
        section = Section.objects.get(id=new_section.id)
        self.assertEqual(section.heading, 'A test section')

    def test_add_section_in_section(self):
        section = Section.objects.create(heading='Test section', instance=self.instance)
        resp = self.client.post('/section/add', {
            'parent': section.id,
            'heading': 'A test subsection'
        })
        new_section = Section.objects.order_by('-id')[0]
        self.assertRedirects(resp, '/%s/%s' % (section.slug, new_section.slug))
        # Check in db
        subsection = Section.objects.get(id=new_section.id)
        self.assertEqual(subsection.heading, 'A test subsection')
        self.assertEqual(subsection.parent, section)

    def test_section_page_lists_speeches(self):
        section = Section.objects.create(heading='A test section', instance=self.instance)
        subsection = Section.objects.create(heading='A test subsection', parent=section, instance=self.instance)

        # Assert no speeches
        resp = self.client.get('/section/%d' % subsection.id)
        self.assertSequenceEqual([], list(resp.context['section_tree']))

        speech = Speech.objects.create(
            text="A test speech",
            section=subsection,
            instance=self.instance,
            start_date=date(2014, 9, 17),
            )
        resp = self.client.get('/section/%d' % subsection.id)
        self.assertSequenceEqual(
            [(speech, {'speech': True, 'new_level': True, 'closed_levels': [1]})],
            list(resp.context['section_tree']))

        # Check that a second speech on the same date doesn't display a date
        Speech.objects.create(
            text="Second speech",
            section=subsection,
            instance=self.instance,
            start_date=date(2014, 9, 17),
            )
        Speech.objects.create(
            text="Next day speech",
            section=subsection,
            instance=self.instance,
            start_date=date(2014, 9, 18),
            )

        # Check that a section page which returns more than one speech on the
        # same date displays the date once.
        resp = self.client.get('/section/%d' % subsection.id)
        self.assertEqual(
            len(re.findall(
                r'<span class="speech__meta-data__date">\s*1[7,8] Sep 2014\s*</span>',
                resp.content.decode())),
            2)
        self.assertContains(resp, 'Next day speech')

    def test_section_page_lists_subsections(self):
        section = Section.objects.create(heading='A test section', instance=self.instance)

        # Assert no subsections
        resp = self.client.get('/section/%d' % section.id)
        self.assertSequenceEqual([], resp.context['section'].get_descendants)

        subsection = Section.objects.create(heading="A test subsection", parent=section, instance=self.instance)
        resp = self.client.get('/section/%d' % section.id)
        self.assertSequenceEqual([subsection], resp.context['section'].get_descendants)

    def test_section_page_has_buttons_to_edit(self):
        # Add a section
        section = Section.objects.create(heading='A test section', instance=self.instance)

        # Call the section's page
        resp = self.client.get('/section/%d' % section.id)

        self.assertContains(
            resp, '<a href="/speech/add?section=%d" class="button small right">Add speech</a>' % section.id,
            html=True)
        self.assertContains(
            resp,
            '<a href="/section/add?section=%d" class="button secondary small right">Add subsection</a>' % section.id,
            html=True)
        self.assertContains(
            resp, '<a href="/section/%d/edit" class="button secondary small right">Edit section</a>' % section.id,
            html=True)

    def test_section_deletion(self):
        # Set up the section
        section = Section.objects.create(heading='A test section', instance=self.instance)
        speech = Speech.objects.create(text="A test speech", section=section, instance=self.instance)
        resp = self.client.get('/section/%d' % section.id)
        self.assertSequenceEqual(
            [(speech, {'speech': True, 'new_level': True, 'closed_levels': [1]})],
            list(resp.context['section_tree']))

        # GET form (confirmation page)
        resp = self.client.get(section.get_delete_url())
        self.assertContains(resp, '<input type="submit" value="Confirm delete?"')

        section_db = Section.objects.get(id=section.id)
        self.assertEqual(section, section_db)

        speech_db = Speech.objects.get(id=speech.id)
        self.assertEqual(speech_db.section_id, section.id)

        # POST form (do the deletion)
        resp = self.client.post(section.get_delete_url())

        self.assertRedirects(resp, '/speeches')

        self.assertEqual(Section.objects.filter(id=section.id).count(), 0)

        speech_db = Speech.objects.get(id=speech.id)
        self.assertEqual(speech_db.section_id, None)

    def test_section_in_other_instance(self):
        other_instance = Instance.objects.create(label='other')
        section = Section.objects.create(heading='A test section', instance=other_instance)
        self.assertEqual(section.slug, 'a-test-section')
        section = Section.objects.create(heading='A test section', instance=self.instance)
        self.assertEqual(section.slug, 'a-test-section')
        section = Section.objects.create(heading='A test section', instance=other_instance)
        self.assertEqual(section.slug, 'a-test-section-2')
        resp = self.client.get('/a-test-section-2')
        self.assertContains(resp, 'Not Found', status_code=404)
