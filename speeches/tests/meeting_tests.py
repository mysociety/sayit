from instances.tests import InstanceTestCase

from speeches.models import Meeting, Debate

class MeetingTests(InstanceTestCase):
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

    def test_meeting_page_lists_debates(self):
        # Add a meeting
        meeting = Meeting.objects.create(title='A test meeting', instance=self.instance)

        # Call the meetings page
        resp = self.client.get('/meeting/1')

        # Assert no debates 
        self.assertSequenceEqual([], resp.context['debate_list'])

        # Add a debate
        debate = Debate.objects.create(title="A test debate", meeting=meeting, instance=self.instance)

        # Call the meetings page again 
        resp = self.client.get('/meeting/1')

        self.assertSequenceEqual([debate], resp.context['debate_list'])

    def test_meeting_page_has_button_to_add_debate(self):
        # Add a meeting
        meeting = Meeting.objects.create(title='A test meeting', instance=self.instance)

        # Call the meetings page
        resp = self.client.get('/meeting/1')

        self.assertContains(resp, '<a class="btn" href="/debate/add?meeting=1">Add a new debate in this meeting</a>', html=True)
