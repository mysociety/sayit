from instances.models import Instance
from instances.tests import InstanceTestCase

from speeches.models import Debate, Meeting, Speech

class DebateTests(InstanceTestCase):
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
        meeting = Meeting.objects.create(title='Test meeting', instance=self.instance)
        resp = self.client.post('/debate/add', {
            'meeting': 1,
            'title': 'A test debate'
        })
        self.assertRedirects(resp, 'debate/1')
        # Check in db
        debate = Debate.objects.get(id=1)
        self.assertEquals(debate.title, 'A test debate')
        self.assertEquals(debate.meeting, meeting)

    def test_debate_page_lists_speeches(self):
        # Add a meeting
        meeting = Meeting.objects.create(title='A test meeting', instance=self.instance)
        # Add a debate
        debate = Debate.objects.create(title='A test debate', meeting=meeting, instance=self.instance)

        # Call the debate's page
        resp = self.client.get('/debate/1')

        # Assert no speeches
        self.assertSequenceEqual([], resp.context['speech_list'])

        # Add a speech
        speech = Speech.objects.create(text="A test speech", debate=debate, instance=self.instance)

        # Call the debate's page again 
        resp = self.client.get('/debate/1')

        self.assertSequenceEqual([speech], resp.context['speech_list'])

    def test_debate_page_has_button_to_add_speech(self):
        # Add a debate
        debate = Debate.objects.create(title='A test debate', instance=self.instance)

        # Call the debate's page
        resp = self.client.get('/debate/1')

        self.assertContains(resp, '<a class="btn" href="/speech/add?debate=1">Add a new speech in this debate</a>', html=True)
