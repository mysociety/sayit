import random

from django.test import TestCase

from speeches.models import cache


class CacheTest(object):
    @cache
    def random(self):
        # return a different value each time, if not cached
        return random.random()


class CacheTests(TestCase):

    def test_caching(self):

        # Create an object, ensure that the caching occurs.
        cachetest1 = CacheTest()
        rand1 = cachetest1.random
        rand2 = cachetest1.random
        self.assertEqual(rand1, rand2)

        # Create another object, check new value cached.
        cachetest2 = CacheTest()
        rand3 = cachetest2.random
        self.assertNotEqual(rand1, rand3)
