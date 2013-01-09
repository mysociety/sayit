from django.test import TestCase

from speeches.models import Meeting

class MeetingTests(TestCase):
    """Tests for the meetings functionality"""

    def test_add_meeting_fails_on_empty_form(self):
        # Test that the form won't submit if empty
        resp = self.client.post('/meeting/add')
        self.assertFormError(resp, 'form', 'title', 'This field is required.')

    def test_add_meeting_with_title(self):
        resp = self.client.post('/meeting/add', {
            'title': 'A test meeting'
        })
        self.assertRedirects(resp, 'meeting/1')
        # Check in db
        meeting = Meeting.objects.get(id=1)
        self.assertEquals(meeting.title, 'A test meeting')