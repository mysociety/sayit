from django.test import TestCase

from speeches.models import Debate, Meeting

class DebateTests(TestCase):
    """Tests for the debate functionality"""

    def test_add_debate_fails_on_empty_form(self):
        # Test that the form won't submit if empty
        resp = self.client.post('/debate/add')
        self.assertFormError(resp, 'form', 'title', 'This field is required.')

    def test_add_debate_with_title(self):
        resp = self.client.post('/debate/add', {
            'title': 'A test debate'
        })
        self.assertRedirects(resp, 'debate/1')
        # Check in db
        debate = Debate.objects.get(id=1)
        self.assertEquals(debate.title, 'A test debate')

    def test_add_debate_in_meeting(self):
        # Add a meeting first
        meeting = Meeting.objects.create(title='Test meeting')
        resp = self.client.post('/debate/add', {
            'meeting': 1,
            'title': 'A test debate'
        })
        self.assertRedirects(resp, 'debate/1')
        # Check in db
        debate = Debate.objects.get(id=1)
        self.assertEquals(debate.title, 'A test debate')
        self.assertEquals(debate.meeting, meeting)