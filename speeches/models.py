from django.db import models
from django.utils import timezone

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

# TODO Meeting needed, or hierarchy of Debate enough? What metadata is there?
#class Meeting(AuditedModel):
#    title = models.CharField()
#    start = models.DateTimeField()
#    end = models.DateTimeField()

#class Debate(AuditedModel):
#    meeting = models.ForeignKey(Meeting, blank=True, null=True)
#    parent = models.ForeignKey(self)
#    start = models.DateTimeField()
#    end = models.DateTimeField()
#    heading
#    subheading

# Speaker - someone who gave a speech
class Speaker(AuditedModel):
    popit_id = models.TextField(unique=True)
    name = models.TextField(db_index=True)

    def __unicode__(self):
        out = "null"
        if self.name : out = '%s' % self.name
        return out

# Speech that a speaker gave
class Speech(AuditedModel):
    # The speech. Need to check have at least one of the following two (preferably both).
    audio = models.FileField(upload_to='speeches/%Y-%m-%d/', max_length=255, blank=True)
    text = models.TextField(blank=True, db_index=True, help_text='The text of the speech')

    # What the speech is part of.
    # The below should really all be on the parents
    # debate = models.ForeignKey(Debate, blank=True, null=True)
    title = models.TextField(blank=True, help_text='The title of the speech, if relevant')
    event = models.TextField(db_index=True, blank=True, help_text='Was the speech at a particular event?')
    location = models.TextField(db_index=True, blank=True, help_text='Where the speech took place')

    # Metadata on the speech
    # type = models.ChoiceField() # speech, scene, narrative, summary, etc.
    speaker = models.ForeignKey(Speaker, blank=True, null=True, help_text='Who gave this speech?', on_delete=models.SET_NULL)
    start = models.DateTimeField(blank=True, null=True, help_text='What time did the speech start?')
    end = models.DateTimeField(blank=True, null=True, help_text='The time the speech ended.')

    # What if source material has multiple speeches, same timestamp - need a way of ordering them?
    # pos = models.IntegerField()

    source_url = models.TextField(blank=True)
    # source_column? Any other source based things?

    class Meta:
        verbose_name_plural = 'speeches'

    def __unicode__(self):
        out = 'Speech'
        if self.title: out += ', %s,' % self.title
        if self.speaker: out += ' by %s' % self.speaker
        if self.start: out += ' at %s' % self.start
        if self.text: out += ' (with text)'
        if self.audio: out += ' (with audio)'
        return out

    @models.permalink
    def get_absolute_url(self):
        return ( 'speech-view', (), { 'pk': self.id } )

    @models.permalink
    def get_edit_url(self):
        return ( 'speech-edit', (), { 'pk': self.id } )
