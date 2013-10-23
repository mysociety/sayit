from datetime import datetime, date, time, timedelta

from speeches.models import Section, Speech
from instances.models import Instance


def create_sections( subsections, parent=None):
    """
    Create a hierachy of sections and speeches. Very useful for setting up test data as needed.

    Note - used in external packages (pombola.south_africa), alter with care.

    create_sections([
        {
            'title': "Top level section",
            'subsections': [
                {   'title': "Nested section",
                    'subsections': [
                        {   'title': "Section with speeches",
                            'speeches': [ 4, date(2013, 3, 25), time(9, 0) ],
                        },
                        {   'title': "Bill on Silly Walks",
                            'speeches': [ 2, date(2013, 3, 25), time(12, 0) ],
                        },
                    ]
                },
                {
                    'title': "Ahother nested section (but completely empty)",
                    'subsections': []
                },
            ]
        },
    ])
    """

    if parent:
        instance = parent.instance
    else:
        instance, _ = Instance.objects.get_or_create(label='whatever')

    for subsection in subsections:
        s = Section.objects.create( instance=instance, title=subsection['title'], parent=parent )
        if 'subsections' in subsection:
            create_sections(subsection['subsections'], s)
        if 'speeches' in subsection:
            num, d, t = subsection['speeches']
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
