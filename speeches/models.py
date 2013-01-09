from django.db import models
from django.utils import timezone
from django.conf import settings

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

class Meeting(AuditedModel):
    title = models.CharField(max_length=255, blank=False, null=False)

    @models.permalink
    def get_absolute_url(self):
        return ( 'meeting-view', (), { 'pk': self.id } )

    @models.permalink
    def get_edit_url(self):
        return ( 'meeting-edit', (), { 'pk': self.id } )

class Debate(AuditedModel):
    meeting = models.ForeignKey(Meeting, blank=True, null=True)
    title = models.CharField(max_length=255, blank=False, null=False)

# SpeakerManager, so that we can define get_by_natural_key()
class SpeakerManager(models.Manager):
    def get_by_natural_key(self, popit_url):
        return self.get(popit_url=popit_url)

# Speaker - someone who gave a speech
class Speaker(AuditedModel):
    popit_url = models.TextField(unique=True)
    name = models.TextField(db_index=True)

    def __unicode__(self):
        out = "null"
        if self.name : out = '%s' % self.name
        return out

    def natural_key(self):
        return (self.popit_url,)

# Speech that a speaker gave
class Speech(AuditedModel):
    # The speech. Need to check have at least one of the following two (preferably both).
    audio = models.FileField(upload_to='speeches/%Y-%m-%d/', max_length=255, blank=True)
    # TODO - we will want to do full text search at some point, so we need an index on
    # this field in some way, but The Right Thing looks complicated, and the current method breaks
    # on really big text.  Since we don't have search at all at the moment, I've removed
    # the basic index completely for now.
    text = models.TextField(blank=True, db_index=False, help_text='The text of the speech')

    # What the speech is part of.
    # The below should really all be on the parents
    # debate = models.ForeignKey(Debate, blank=True, null=True)
    title = models.TextField(blank=True, help_text='The title of the speech, if relevant')
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
