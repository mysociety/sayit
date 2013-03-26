from datetime import datetime, date, time, timedelta

from django.test import TestCase

from speeches.models import Section, Speech
from instances.models import Instance

class SectionTests(TestCase):

    def create_sections(self, node, parent=None):
        if parent:
            instance = parent.instance
        else:
            instance, _ = Instance.objects.get_or_create(label='whatever')

        for key, item in node.items():
            s = Section.objects.create( instance=instance, title=key, parent=parent )
            if isinstance(item, dict):
                self.create_sections(item, s)
            else:
                num, d, t = item
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
        self.create_sections({
            "Government Debates": {
                "Monday 25th March": {
                    "Oral Answers to Questions - Silly Walks": [ 4, date(2013, 3, 25), time(9, 0) ],
                    "Bill on Silly Walks": [ 2, date(2013, 3, 25), time(12, 0) ],
                },
                "Friday 29th March": {
                    "Fixed Easter Bill": {
                        "New Clause 1": [ 3, date(2013, 3, 29), time(14, 0) ],
                        "Clause 1": [ 3, date(2013, 3, 29), time(14, 30) ],
                        "Z Clause": [ 2, date(2013, 3, 29), time(15, 00) ],
                    },
                },
            },
            "Government Written Answers": {
                "Ministry of Silly Walks": {
                    "Wednesday 6th of March": [ 1, date(2013, 3, 6), None ],
                    "Thursday 7th of March": [ 2, date(2013, 3, 7), None ],
                },
                "Ministry of Aardvarks": {},
                "Ministry of Something Else": {},
            },
        })

    def test_datetimes(self):
        section = Section.objects.get(title="Bill on Silly Walks")
        dts = sorted(section.speech_datetimes())
        self.assertEqual(dts[0], datetime(2013, 3, 25, 12, 0))
        self.assertEqual(dts[1], datetime(2013, 3, 25, 12, 10))

    def test_section_creation(self):

        # Get the top level section:
        top_level = Section.objects.get(title='Government Written Answers', level=0)

        all_sections = top_level.get_descendants(include_self=True)

        self.assertEqual(len(all_sections),
                         6,
                         "The total number of sections was wrong")

        all_ministries = top_level.get_children()

        self.assertEqual(len(all_ministries),
                         3,
                         "The number of ministries was wrong")

        # Check that the sections are sorted by title:
        all_ministries = [ a.title.replace('Ministry of ', '') for a in all_ministries ]
        self.assertEqual(all_ministries, [ 'Aardvarks', 'Silly Walks', 'Something Else' ])

        # Get all speeches under a section, where everything should be
        # sorted by speech date:
        top_level = Section.objects.get(title="Government Debates")
        children = top_level.get_descendants_ordered_by_earliest_speech(include_self=False)
        children = [ c.title for c in children ]
        self.assertEqual(children, [ 'Monday 25th March', 'Oral Answers to Questions - Silly Walks', 'Bill on Silly Walks', 'Friday 29th March', 'Fixed Easter Bill', 'New Clause 1', 'Clause 1', 'Z Clause' ])

