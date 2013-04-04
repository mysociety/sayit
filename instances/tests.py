from django.test import TestCase, LiveServerTestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.core.validators import ValidationError
from django.contrib.auth.models import User

from .models import Instance

FAKE_URL = 'testing.example.org:8000'

class InstanceClient(Client):
    def get(self, *args, **kwargs):
        kwargs['HTTP_HOST'] = FAKE_URL
        return super(InstanceClient, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        kwargs['HTTP_HOST'] = FAKE_URL
        return super(InstanceClient, self).post(*args, **kwargs)

@override_settings(
    BASE_HOST='example.org',
    PASSWORD_HASHERS = ( 'django.contrib.auth.hashers.MD5PasswordHasher', ),
)
class InstanceTestCase(TestCase):
    client_class = InstanceClient

    def setUp(self):
        self.instance = Instance.objects.create(label='testing')
        user = User.objects.create_user(username='admin', email='admin@example.org', password='admin')
        user.instances.add(self.instance)
        self.client.login(username='admin', password='admin')

    def assertRedirects(self, *args, **kwargs):
        kwargs['host'] = FAKE_URL
        return super(InstanceTestCase, self).assertRedirects(*args, **kwargs)

@override_settings( SESSION_COOKIE_DOMAIN='127.0.0.1.xip.io' )
class InstanceLiveServerTestCase(LiveServerTestCase):
    def setUp(self):
        self.instance = Instance.objects.create(label='testing')
        user = User.objects.create_user(username='admin', email='admin@example.org', password='admin')
        user.instances.add(self.instance)

        self.selenium.get('%s%s' % (self.live_server_url, '/accounts/login/?next=/'))
        username_input = self.selenium.find_element_by_name("username")
        username_input.send_keys('admin')
        password_input = self.selenium.find_element_by_name("password")
        password_input.send_keys('admin')
        self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()

# ---

class SimpleTest(TestCase):
    def test_instance_lower_casing(self):
        i = Instance(label='HELLO')
        self.assertEqual(i.label, 'hello')

    def test_bad_label(self):
        self.assertRaises(ValidationError, lambda: Instance(label='Spaces are not allowed'))
        self.assertRaises(ValidationError, lambda: Instance(label='Nor-a-symbol-such-as-^'))
        self.assertRaises(ValidationError, lambda: Instance(label="Nor-can-you-end-with--"))

