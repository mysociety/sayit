import calendar
import logging
import os

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.files import File

from instances.models import InstanceMixin
import speeches
from speeches.utils import AudioHelper

logger = logging.getLogger(__name__)

class AuditedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        now = timezone.now()
        if not self.id:
            self.created = now
        self.modified = now
        super(AuditedModel, self).save(*args, **kwargs)

class Meeting(InstanceMixin, AuditedModel):
    title = models.CharField(max_length=255, blank=False, null=False)
    date = models.DateField(blank=True, null=True, help_text='When date did the meeting happen?')

    @models.permalink
    def get_absolute_url(self):
        return ( 'meeting-view', (), { 'pk': self.id } )

    @models.permalink
    def get_edit_url(self):
        return ( 'meeting-edit', (), { 'pk': self.id } )

    def __unicode__(self):
        return self.title

class Debate(InstanceMixin, AuditedModel):
    meeting = models.ForeignKey(Meeting, blank=True, null=True)
    title = models.CharField(max_length=255, blank=False, null=False)

    @models.permalink
    def get_absolute_url(self):
        return ( 'debate-view', (), { 'pk': self.id } )

    @models.permalink
    def get_edit_url(self):
        return ( 'debate-edit', (), { 'pk': self.id } )

    def __unicode__(self):
        return self.title

# SpeakerManager
class SpeakerManager(models.Manager):

    # Get or create a speaker from a popit_url
    # TODO - we need to do the create bit
    def get_or_create_from_popit_url(self, popit_url):
        speaker = None
        if popit_url:
            try:
                speaker = self.get(popit_url=popit_url)
            except Speaker.DoesNotExist:
                # TODO - lookup the speaker from the popit url
                # For now we will trust the sender, and do it right now...
                logger.error('Speaker: {0} does not exist in db, setting to None'.format(popit_url))
                speaker = None
        return speaker

    # Define get_by_natural_key so that we can refer to speakers by their
    # popit_url instead of our local primary key id
    def get_by_natural_key(self, popit_url):
        return self.get(popit_url=popit_url)

# Speaker - someone who gave a speech
class Speaker(InstanceMixin, AuditedModel):
    popit_url = models.TextField(unique=True)
    name = models.TextField(db_index=True)
    objects = SpeakerManager()

    def __unicode__(self):
        out = "null"
        if self.name : out = '%s' % self.name
        return out

    def natural_key(self):
        return (self.popit_url,)

# Speech manager
class SpeechManager(models.Manager):

    def create_from_recording(self, recording):
        """Create one or more speeches from a recording. If there's no audio"""
        created_speeches = []

        # Split the recording's audio files
        audio_helper = AudioHelper()
        audio_files = audio_helper.split_recording(recording)

        # Create a speech for each one of the audio files
        sorted_timestamps = recording.timestamps.order_by("timestamp")
        for index, audio_file in enumerate(audio_files):
            speaker = None
            start_date = None
            start_time = None
            end_date = None
            end_time = None

            # Get the related timestamp, if any.
            if sorted_timestamps and len(sorted_timestamps) > 0:
                # We assume that the files are returned in order of timestamp
                timestamp = sorted_timestamps[index]
                speaker = timestamp.speaker
                start_date = timestamp.timestamp.date()
                start_time = timestamp.timestamp.time()
                # If there's another one we can work out the end too
                if index < len(sorted_timestamps) - 1:
                    next_timestamp = sorted_timestamps[index + 1]
                    end_date = next_timestamp.timestamp.date()
                    end_time = next_timestamp.timestamp.time()

            created_speeches.append(self.create(
                audio=File(open(audio_file)),
                speaker=speaker,
                start_date=start_date,
                start_time=start_time,
                end_date=end_date,
                end_time=end_time
            ))

        return created_speeches


# Speech that a speaker gave
class Speech(InstanceMixin, AuditedModel):
    # Custom manager
    objects = SpeechManager()

    # The speech. Need to check have at least one of the following two (preferably both).
    audio = models.FileField(upload_to='speeches/%Y-%m-%d/', max_length=255, blank=True)
    # TODO - we will want to do full text search at some point, so we need an index on
    # this field in some way, but The Right Thing looks complicated, and the current method breaks
    # on really big text.  Since we don't have search at all at the moment, I've removed
    # the basic index completely for now.
    text = models.TextField(blank=True, db_index=False, help_text='The text of the speech')

    # What the speech is part of.
    debate = models.ForeignKey(Debate, blank=True, null=True)
    title = models.TextField(blank=True, help_text='The title of the speech, if relevant')
    # The below two fields could be on the debate if we made it a required field of a speech
    event = models.TextField(db_index=True, blank=True, help_text='Was the speech at a particular event?')
    location = models.TextField(db_index=True, blank=True, help_text='Where the speech took place')

    # Metadata on the speech
    # type = models.ChoiceField() # speech, scene, narrative, summary, etc.
    speaker = models.ForeignKey(Speaker, blank=True, null=True, help_text='Who gave this speech?', on_delete=models.SET_NULL)

    start_date = models.DateField(blank=True, null=True, help_text='What date did the speech start?')
    start_time = models.TimeField(blank=True, null=True, help_text='What time did the speech start?')

    end_date = models.DateField(blank=True, null=True, help_text='What date did the speech end?')
    end_time = models.TimeField(blank=True, null=True, help_text='What time did the speech end?')

    # What if source material has multiple speeches, same timestamp - need a way of ordering them?
    # pos = models.IntegerField()

    source_url = models.TextField(blank=True)
    # source_column? Any other source based things?

    # Task id for celery transcription tasks
    celery_task_id = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'speeches'

    def __unicode__(self):
        out = 'Speech'
        if self.title: out += ', %s,' % self.title
        if self.speaker: out += ' by %s' % self.speaker
        if self.start_date: out += ' at %s' % self.start_date
        if self.text: out += ' (with text)'
        if self.audio: out += ' (with audio)'
        return out

    @property
    def summary(self):
        summary_length = settings.SPEECH_SUMMARY_LENGTH
        default_transcription = settings.DEFAULT_TRANSCRIPTION
        if self.audio and (not self.text or self.text == default_transcription):
            return "[ recorded audio ]"
        else:
            return self.text[:summary_length] + '...' if len(self.text) > summary_length else self.text

    @models.permalink
    def get_absolute_url(self):
        return ( 'speech-view', (), { 'pk': self.id } )

    @models.permalink
    def get_edit_url(self):
        return ( 'speech-edit', (), { 'pk': self.id } )

    def save(self, *args, **kwargs):
        """Overriden save method to automatically convert the audio to an mp3"""

        # If we have an audio file and it's not an mp3, make it one
        if self.audio and not self.audio.name.lower().endswith('.mp3'):
            if not os.path.exists(self.audio.path):
                # If it doesn't already exist, save the old audio first so that we can re-encode it
                # This is needed if it's newly uploaded
                self.audio.save(self.audio.name, File(self.audio), False)
            # Transcode the audio into mp3
            audio_helper = speeches.utils.AudioHelper()
            mp3_filename = audio_helper.make_mp3(self.audio.path)
            mp3_file = open(mp3_filename, 'rb')
            # Delete the old file
            self.audio.delete(False)
            # Save the mp3 as the new file
            self.audio.save(mp3_file.name, File(mp3_file), False)

        # Call the original model save to do everything
        super(Speech, self).save(*args, **kwargs)

    def start_transcribing(self):
        """Kick off a celery task to transcribe this speech"""
        # We only do anything if there's no text already
        if not self.text:
            # If someone is adding a new audio file and there's already a task
            # We need to clear it
            if self.celery_task_id:
                celery.task.control.revoke(self.celery_task_id)
            # Now we can start a new one
            result = speeches.tasks.transcribe_speech.delay(self.id)
            # Finally, we can remember the new task in the model
            self.celery_task_id = result.task_id
            self.save()

# A timestamp of a particular speaker at a particular time.
# Used to record events like "This speaker started speaking at 00:33"
# in a specific recording, before it's chopped up into a speech
class RecordingTimestamp(InstanceMixin, AuditedModel):
    speaker = models.ForeignKey(Speaker, blank=True, null=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(db_index=True, blank=False)

    @property
    def utc(self):
        """Return our timestamp as a UTC long"""
        return calendar.timegm(self.timestamp.timetuple())

# A raw recording, might be divided up into multiple speeches
class Recording(InstanceMixin, AuditedModel):
    audio = models.FileField(upload_to='recordings/%Y-%m-%d/', max_length=255, blank=False)
    timestamps = models.ManyToManyField(RecordingTimestamp, blank=True, null=True)
