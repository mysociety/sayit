from django.test import TestCase

from speeches.models import Section, Speech
from instances.models import Instance

from datetime import date, time

class SectionTests(TestCase):

    def create_sections(self):

        instance = Instance.objects.create(label='whatever')
        top_level = Section.objects.create(
            instance=instance,
            title="Government Written Answers")
        sub_level_si = Section.objects.create(
            instance=instance,
            title="Ministry of Silly Walks",
            parent=top_level)
        sub_sub_level_b = Section.objects.create(
            instance=instance,
            title="Thursday 7th of March",
            parent=sub_level_si)
        sub_sub_level = Section.objects.create(
            instance=instance,
            title="Wednesday 6th of March",
            parent=sub_level_si)
        sub_level_aa = Section.objects.create(
            instance=instance,
            title="Ministry of Aardvarks",
            parent=top_level)
        sub_level_so = Section.objects.create(
            instance=instance,
            title="Ministry of Something Else",
            parent=top_level)

        # Attach speeches to some of these sections:
        Speech.objects.create(instance=instance,
                              text='An early example speech, rhubarb rhubarb',
                              start_date=date(2013, 3, 7),
                              start_time=time(9, 0),
                              section=sub_sub_level_b)
        Speech.objects.create(instance=instance,
                              text='A later example speech, blah blah blah',
                              start_date=date(2013, 3, 7),
                              start_time=time(9, 30),
                              section=sub_sub_level_b)
        Speech.objects.create(instance=instance,
                              text='A speech on the previous day that goes on and on',
                              start_date=date(2013, 3, 6),
                              start_time=time(9, 0),
                              section=sub_sub_level)

    def setUp(self):
        self.create_sections()

    def test_section_creation(self):

        # Get the top level section:

        top_level = Section.objects.get(level=0)

        all_sections = top_level.get_descendants(include_self=True)

        self.assertEqual(len(all_sections),
                         6,
                         "The total number of sections was wrong")

        all_ministries = top_level.get_children()

        self.assertEqual(len(all_ministries),
                         3,
                         "The number of ministries was wrong")

        # Check that the sections are sorted by title:

        self.assertTrue("Aardvarks" in all_ministries[0].title,
                        u"The first ministry should be Aardvarks; that wasn't found in '%s'" % (all_ministries[0].title,))
        self.assertTrue("Silly Walk" in all_ministries[1].title,
                        u"The second ministry should be Silly Walks; that wasn't found in '%s'" % (all_ministries[1].title,))
        self.assertTrue("Something Else" in all_ministries[2].title,
                        u"The last ministry should be Something Else; that wasn't found in '%s'" % (all_ministries[2].title,))
