from django.test import TestCase
from django.core.validators import ValidationError

from .models import Instance

class SimpleTest(TestCase):
    def test_instance_lower_casing(self):
        i = Instance(label='HELLO')
        self.assertEqual(i.label, 'hello')

    def test_bad_label(self):
        self.assertRaises(ValidationError, lambda: Instance(label='Spaces are not allowed'))
        self.assertRaises(ValidationError, lambda: Instance(label='Nor-a-symbol-such-as-^'))
        self.assertRaises(ValidationError, lambda: Instance(label="Nor-can-you-end-with--"))

