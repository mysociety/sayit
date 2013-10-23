from datetime import datetime, date, time, timedelta

from speeches.models import Section, Speech
from instances.models import Instance


def create_sections( node, parent=None):
    """
    Create a hierachy of sections and speeches. Very useful for setting up test data as needed.

    Note - used in external packages (pombola.south_africa), alter with care.

    create_sections([
        {
            'title': "Top level section",
            'items': [
                {   'title': "Nested section",
                    'items': [
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
                    'items': []
                },
            ]
        },
    ])
    """

    if parent:
        instance = parent.instance
    else:
        instance, _ = Instance.objects.get_or_create(label='whatever')

    for item in node:
        s = Section.objects.create( instance=instance, title=item['title'], parent=parent )
        if 'items' in item:
            create_sections(item['items'], s)
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
