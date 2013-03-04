from django.test import TestCase, LiveServerTestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.core.validators import ValidationError

from .models import Instance

FAKE_URL = 'testing.example.org:8000'

class InstanceClient(Client):
    def get(self, *args, **kwargs):
        kwargs['HTTP_HOST'] = FAKE_URL
        return super(InstanceClient, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        kwargs['HTTP_HOST'] = FAKE_URL
        return super(InstanceClient, self).post(*args, **kwargs)

@override_settings( BASE_HOST='example.org' )
class InstanceTestCase(TestCase):
    client_class = InstanceClient

    def setUp(self):
        self.instance = Instance.objects.create(label='testing')

    def assertRedirects(self, *args, **kwargs):
        kwargs['host'] = FAKE_URL
        return super(InstanceTestCase, self).assertRedirects(*args, **kwargs)

class InstanceLiveServerTestCase(LiveServerTestCase):
    def setUp(self):
        self.instance = Instance.objects.create(label='testing')

# ---

class SimpleTest(TestCase):
    def test_instance_lower_casing(self):
        i = Instance(label='HELLO')
        self.assertEqual(i.label, 'hello')

    def test_bad_label(self):
        self.assertRaises(ValidationError, lambda: Instance(label='Spaces are not allowed'))
        self.assertRaises(ValidationError, lambda: Instance(label='Nor-a-symbol-such-as-^'))
        self.assertRaises(ValidationError, lambda: Instance(label="Nor-can-you-end-with--"))

