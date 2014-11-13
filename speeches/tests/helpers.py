import tempfile
import shutil

from datetime import datetime, date, timedelta

from django.test import TestCase
from django.test.utils import override_settings

from selenium.webdriver.support.ui import WebDriverWait

from speeches.models import Section, Speech
from instances.models import Instance

from instances.tests import InstanceTestCase, InstanceLiveServerTestCase


class InstanceTestCase(InstanceTestCase):
    default_instance_options = dict(label='default')


temp_media_root = tempfile.mkdtemp(prefix='sayit_test')


@override_settings(MEDIA_ROOT=temp_media_root)
class OverrideMediaRootMixin(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(temp_media_root)
        return super(OverrideMediaRootMixin, cls).tearDownClass()


class InstanceLiveServerTestCase(InstanceLiveServerTestCase):
    default_instance_options = dict(label='default')

    def setUp(self):
        super(InstanceLiveServerTestCase, self).setUp()
        WebDriverWait(self.selenium, 10).until(
            lambda x: x.find_element_by_link_text('Add your first statement')
        )


class ParentInstanceMismatchError(Exception):
    pass


def create_sections(subsections, parent=None, instance=None):
    """
    Create a hierachy of sections and speeches - good for setting up test data.

    Note - used in external packages (pombola.south_africa), alter with care.

    create_sections([
        {
            'heading': "Top level section",
            'subsections': [
                {   'heading': "Nested section",
                    'subsections': [
                        {   'heading': "Section with speeches",
                            'speeches': [ 4, date(2013, 3, 25), time(9, 0) ],
                        },
                        {   'heading': "Bill on Silly Walks",
                            'speeches': [ 2, date(2013, 3, 25), time(12, 0) ],
                        },
                    ]
                },
                {
                    'heading': "Another nested section (but completely empty)",
                    'subsections': []
                },
            ]
        },
    ])
    """

    # If given an instance and a parent check that they are compatible -
    # we don't want to end up with a hierarchy that spans instances and
    # this would probably mean that there is some confusion upstream that
    # we should highlight.
    if instance and parent and instance != parent.instance:
        raise ParentInstanceMismatchError(
            "The instance and parent.instance do not match")

    # If we have a parent then use the instance from that.
    if parent:
        instance = parent.instance

    # If we don't have an instance (which also means we had no parent)
    # then create one - this is very convenient in the test scripts.
    if not instance:
        instance, _ = Instance.objects.get_or_create(label='create-sections-instance')

    for subsection in subsections:
        s = Section.objects.create(
            instance=instance,
            heading=subsection['heading'],
            parent=parent,
            )
        if 'subsections' in subsection:
            create_sections(subsection['subsections'], parent=s)
        if 'speeches' in subsection:
            # If there's a 4th element in speeches, that's a boolean
            # indicating whether the speeches should be public:
            speeches_details = subsection['speeches']
            if len(speeches_details) >= 4:
                public = speeches_details[3]
            else:
                public = True
            num, d, t = speeches_details[:3]
            for i in range(0, num):
                Speech.objects.create(
                    instance=instance,
                    section=s,
                    text='rhubarb rhubarb',
                    start_date=d,
                    start_time=t,
                    public=public,
                    source_url="http://somewhere.or.other/{0}".format(i),
                )
                if t:
                    t = (datetime.combine(date.today(), t) + timedelta(minutes=10)).time()


class CreateSectionsTests(TestCase):
    def test_parent_instance_mismatch(self):
        foo_instance = Instance.objects.create(label="foo")
        bar_instance = Instance.objects.create(label="bar")
        foo_parent = Section.objects.create(
            instance=foo_instance,
            heading="Foo Section",
            )

        # Should run without exception
        create_sections([], parent=foo_parent, instance=foo_instance)
        create_sections([], instance=foo_instance)
        create_sections([], parent=foo_parent)
        create_sections([])

        # Should raise
        self.assertRaises(
            ParentInstanceMismatchError,
            create_sections,
            subsections=[],
            parent=foo_parent,
            instance=bar_instance,
        )
