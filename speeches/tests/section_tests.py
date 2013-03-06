from django.test import TestCase

from speeches.models import Section

class SectionTests(TestCase):

    def create_sections(self):
        top_level = Section.objects.create(title="Government Written Answers")
        sub_level_si = Section.objects.create(title="Ministry of Silly Walks",
                                              parent=top_level)
        sub_sub_level = Section.objects.create(title="Thursday 7th of March",
                                               parent=sub_level_si)
        sub_level_aa = Section.objects.create(title="Ministry of Aardvarks",
                                              parent=top_level)
        sub_level_so = Section.objects.create(title="Ministry of Something Else",
                                              parent=top_level)

    def setUp(self):
        self.create_sections()

    def test_section_creation(self):

        # Get the top level section:

        top_level = Section.objects.get(level=0)

        all_sections = top_level.get_descendants(include_self=True)

        self.assertEqual(len(all_sections),
                          5,
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
