import calendar
import datetime
import hashlib
import logging
import os

from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.html import strip_tags
from django.template.defaultfilters import timesince, slugify
from django.conf import settings
from django.core.files import File
from django.contrib.contenttypes import generic

from instances.models import InstanceMixin, InstanceManager
import speeches
from speeches.utils import AudioHelper
from speeches.utils.base32 import int_to_base32

from djqmethod import Manager, querymethod
from popit.models import Person
from sluggable.fields import SluggableField
from sluggable.models import Slug as SlugModel

logger = logging.getLogger(__name__)

max_date = datetime.date(datetime.MAXYEAR, 12, 31)
max_time = datetime.time(23,59)
max_datetime = datetime.datetime.combine(max_date, max_time)

class cache(object):
    '''Computes attribute value and caches it in the instance.
    Python Cookbook (Denis Otkidach) http://stackoverflow.com/users/168352/denis-otkidach
    This decorator allows you to create a property which can be computed once and
    accessed many times. Sort of like memoization.

    '''
    def __init__(self, method, name=None):
        # record the unbound-method and the name
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__
    def __get__(self, inst, cls):
        # self: <__main__.cache object at 0xb781340c>
        # inst: <__main__.Foo object at 0xb781348c>
        # cls: <class '__main__.Foo'>
        if inst is None:
            # instance attribute accessed on class, return self
            # You get here if you write `Foo.bar`
            return self
        # compute, cache and return the instance's attribute value
        result = self.method(inst)
        # setattr redefines the instance's attribute so this doesn't get called again
        setattr(inst, self.name, result)
        return result

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

class Slug(SlugModel):
    pass

# Speaker - someone who gave a speech
class Speaker(InstanceMixin, AuditedModel):
    person = models.ForeignKey(Person, blank=True, null=True, on_delete=models.PROTECT, help_text='Associated PopIt object, optional')
    name = models.TextField(db_index=True)
    slug = SluggableField(unique_with='instance', populate_from='name')
    slugs = generic.GenericRelation(Slug)

    class Meta:
        ordering = ('name',)
        unique_together = ('instance', 'slug')

    def __unicode__(self):
        if self.name:
            return self.name
        return "[no name]"

    @property
    def colour(self):
        return hashlib.sha1('%s' % (self.person_id or self.id)).hexdigest()[:6]

    @property
    def id32(self):
        return int_to_base32(self.id)

    @models.permalink
    def get_absolute_url(self):
        return ( 'speeches:speaker-view', (), { 'slug': self.slug } )

    @models.permalink
    def get_edit_url(self):
        return ( 'speeches:speaker-edit', (), { 'pk': self.id } )

    # http://stackoverflow.com/a/5772272/669631
    def save(self, *args, **kwargs):
        if self.person:
            conflicting_instance = Speaker.objects.filter(instance=self.instance, person=self.person)
            if self.id:
                conflicting_instance = conflicting_instance.exclude(pk=self.id)
            if conflicting_instance.exists():
                raise Exception('Speaker with this instance and popit person already exists.')
        super(Speaker, self).save(*args, **kwargs)


class Tag(InstanceMixin, AuditedModel):
    name = models.CharField(unique=True, max_length=100)

    def __unicode__(self):
        return self.name


class SectionManager(InstanceManager, Manager):

    def get_or_create_with_parents(self, instance, titles):
        """Get or create the entire hierarchy of sections given, returning the bottom one."""

        # If there are no titles to create we just return None
        if not len(titles):
            return None

        # Get the title to create, the rest and get the parent
        title = titles[-1]
        rest = titles[:-1]
        parent = self.get_or_create_with_parents(instance, rest)
        
        section, created = self.get_or_create(instance=instance, title=title, parent=parent)

        return section


class Section(AuditedModel, InstanceMixin):
    # Custom manager
    objects = SectionManager()

    title = models.TextField(blank=True, help_text=_('The title of the section'))
    description = models.TextField(blank=True, help_text=_('Longer description, HTML'))
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    slug = SluggableField(unique_with=('parent', 'instance'), populate_from='title')
    source_url = models.TextField(blank=True)

    slugs = generic.GenericRelation(Slug)

    class Meta:
        ordering = ('id',)
        unique_together = ('parent', 'slug', 'instance')

    def __unicode__(self):
        return self.title or _('Section')

    def speech_datetimes(self):
        return (datetime.datetime.combine(s.start_date, s.start_time or datetime.time(0,0) )
                for s in self.speech_set.all())

    def is_leaf_node(self):
        return not self.children.exists()

    @cache
    def get_children(self):
        tree = self.get_descendants
        try:
            lvl = tree[0].level
            return [ s for s in tree if s.level == lvl ]
        except:
            return []

    @cache
    def get_ancestors(self):
        # Cached for now, so these aren't supplied as arguments
        ascending = False
        include_self = True
        """Return the ancestors of the current Section, in either direction,
        optionally including itself."""
        dir = ascending and 'ASC' or 'DESC'
        s = Section.objects.raw(
            """WITH RECURSIVE cte AS (
                SELECT speeches_section.*, 1 AS l FROM speeches_section WHERE id=%s
                UNION ALL
                SELECT s.*, l+1 FROM cte JOIN speeches_section s ON cte.parent_id = s.id
            )
            SELECT * FROM cte ORDER BY l """ + dir,
            [ self.id ]
        )
        if not include_self:
            s = ascending and s[1:] or s[:-1]
        return list(s) # So it's evaluated and will be cached

    def _get_descendants(self, include_self=False, include_count='', include_min='', max_depth=''):
        """Return the descendants of the current Section, in depth-first order.
        Optionally, include speech counts, minimum speech times, and only
        descend a certain depth."""
        select = [ '*' ]
        if include_count:
            select.append("(SELECT COUNT(*) FROM speeches_speech WHERE section_id = cte.id) AS speech_count")
        if include_min:
            select.append("(SELECT MIN( start_date + COALESCE(start_time, time '00:00') ) FROM speeches_speech WHERE section_id = cte.id) AS speech_min")
        if max_depth:
            max_depth = "WHERE array_upper(path, 1) < %d" % (max_depth+1)
        s = Section.objects.raw(
            """WITH RECURSIVE cte AS (
                SELECT speeches_section.*, 0 AS level, ARRAY[id] AS path FROM speeches_section WHERE id=%s
                UNION ALL
                SELECT s.*, level+1, cte.path||s.id FROM cte JOIN speeches_section s ON cte.id = s.parent_id
            """ + max_depth + """
            )
            SELECT """ + ','.join(select) + """ FROM cte ORDER BY path""",
            [ self.id ]
        )
        if not include_self:
            s = s[1:]
        return s

    @cache
    def get_descendants_tree(self):
        """Given a flat list of Sections ordered by speech_min, create a
        hierarchical structure containing the same information."""
        d = self._get_descendants_by_speech(include_count=True)
        prev = self
        parents = [ ]
        for node in d:
            if node.level > getattr(prev, 'level', 0):
                parents.append( prev )
                prev._childs = []
            elif node.level < prev.level:
                parents = parents[:node.level-prev.level]
            elif node.path[:-1] != prev.path[:-1]: # Swapping parentage in some way
                sw = ( i for i in xrange(len(node.path)) if node.path[i] != prev.path[i] ).next()
                parents = parents[:sw-node.level]
                for i in range(sw, node.level):
                    section = Section.objects.get(id=node.path[i])
                    section_copy = Section(title=section.title, parent=section.parent)
                    section_copy._childs = []
                    parents[-1]._childs.append( section_copy )
                    parents.append( section_copy )
            prev = node
            parents[-1]._childs.append( node )
        return d

    def get_descendants_tree_with_speeches(self, request, all_speeches=False):
        # Get the descendants tree of sections
        tree = self.get_descendants_tree

        # Fetch all speeches in this section, or all descendant sections
        section_list = [ self ]
        if all_speeches:
            section_list.extend( tree )

        speech_list = Speech.objects.filter(section__in=section_list).visible(request).select_related('speaker').prefetch_related('tags')
        self._speeches_by_section = {}
        for s in speech_list:
            self._speeches_by_section.setdefault(s.section_id, []).append(s)

        self._interleave_speeches(self)

        # Finally, work back into a flat format for template display
        tree_final = []
        def rec(s, l):
            for i, c in enumerate(s._childs):
                attrs = {}
                if i == 0: attrs['new_level'] = True
                if isinstance(c, Speech): attrs['speech'] = True

                tree_final.append( ( c, attrs ) )

                if isinstance(c, Section):
                    rec(c, l+1)

                if i == len(s._childs) - 1:
                    tree_final[-1][1].setdefault('closed_levels', []).append(l)
        rec(self, 1)

        # Return an iterator because otherwise passing this down in context to
        # subtemplates is really slow. I mean, upwards of 30 seconds slow.
        # As a class so it can be reused after use (e.g. by the tests).
        class _iterable(object):
            def __iter__(self):
                return iter(tree_final)
        return _iterable()

    def _interleave_speeches(self, section):
        if not hasattr(section, '_childs'):
            section._childs = []

        # Recurse through the tree
        for child in section._childs:
            self._interleave_speeches(child)

        # Create a sorting key for each entry of the tree
        tree_with_key = [
            (
                (
                    getattr(d, 'speech_min', None) or max_datetime,
                    '',
                    i
                ),
                d
            ) for i, d in enumerate(section._childs)
        ]

        # Create a sorting key for each speech
        speech_list_with_key = [
            (
                (
                    datetime.datetime.combine(
                        s.start_date or max_date, s.start_time or max_time
                    ),
                    s.id
                ),
                s
            ) for s in self._speeches_by_section.get(section.id, [])
        ]

        # Sort by our sorting keys to interleave the two
        tree_sorted = [ s[1] for s in sorted( tree_with_key + speech_list_with_key ) ]
        section._childs = tree_sorted

    @cache
    def get_descendants(self):
        return self._get_descendants_by_speech()

    def _get_descendants_by_speech(self, **kwargs):
        dqs = self._get_descendants(include_min=True, **kwargs)

        lookup = dict((x.id, x) for x in dqs)
        lookup[self.id] = self
        self.speech_min = None

        for d in dqs:
            if not d.speech_min:
                continue
            for parent_id in reversed(d.path):
                parent = lookup[parent_id]
                if not parent.speech_min or d.speech_min < parent.speech_min:
                    parent.speech_min = d.speech_min

        # Set the speech_min to all the earliests
        for d in dqs:
            if d.speech_min: continue
            for parent_id in reversed(d.path):
                parent = lookup[parent_id]
                if parent.speech_min:
                    d.speech_min = parent.speech_min
                    break

        return sorted( dqs, key=lambda s: getattr(s, 'speech_min', datetime.datetime(datetime.MAXYEAR, 12, 31)) )

    @models.permalink
    def get_absolute_url(self):
        return ( 'speeches:section-view', (), { 'full_slug': self.get_path } )

    @models.permalink
    def get_edit_url(self):
        return ( 'speeches:section-edit', (), { 'pk': self.id } )

    @models.permalink
    def get_delete_url(self):
        return ( 'speeches:section-delete', (), { 'pk': self.id } )

    @cache
    def get_path(self):
        return '/'.join([ s.slug for s in self.get_ancestors ])

    def _get_next_previous_node(self, direction):
        if not self.parent:
            return None
        root = self.get_ancestors[0]
        tree = root.get_descendants
        idx = tree.index(self)
        lvl = tree[idx].level
        same_level = [ s for s in tree if s.level == lvl ]
        idx = same_level.index(self)
        if direction == -1 and idx == 0: return None
        try:
            return same_level[idx+direction]
        except:
            return None

    def get_next_node(self):
        """Fetch the next node in the tree, at the same level as this one."""
        return self._get_next_previous_node(1)

    def get_previous_node(self):
        """Fetch the previous node in the tree, at the same level as this one."""
        return self._get_next_previous_node(-1)

    def descendant_speeches(self):
        """Return a queryset of all speeches that belong to this section, or any of its descendants."""
        section_descendants = self._get_descendants(include_self=True)
        section_descendants_ids = [x.id for x in section_descendants]
        return Speech.objects.filter(section__in=section_descendants_ids)


class AudioMP3Mixin(object):
    def save(self, *args, **kwargs):
        """Overriden save method to automatically convert the audio to an mp3"""
        duration = kwargs.pop('duration', None)
        needs_conversion = self.audio and not self.audio.name.lower().endswith('.mp3')

        # If we have an audio file and it's not an mp3, make it one
        if duration or needs_conversion:
            if not os.path.exists(self.audio.path):
                # If it doesn't already exist, save the old audio first so that we can re-encode it
                # This is needed if it's newly uploaded
                self.audio.save(self.audio.name, File(self.audio), save=False)

            audio_helper = speeches.utils.AudioHelper()

            if needs_conversion:
                mp3_filename = audio_helper.make_mp3(self.audio.path)
                mp3_file = open(mp3_filename, 'rb')
                self.audio.save(mp3_file.name, File(mp3_file), save=False)

            if duration:
                self.audio_duration = audio_helper.get_audio_duration(self.audio.path)

        # Call the original model save to do everything
        super(AudioMP3Mixin, self).save(*args, **kwargs)


# Speech manager
class SpeechManager(InstanceManager, Manager):
    pass


# Speech that a speaker gave
class Speech(InstanceMixin, AudioMP3Mixin, AuditedModel):
    # Custom manager
    objects = SpeechManager()

    # The speech. Need to check have at least one of the following two (preferably both).
    audio = models.FileField(upload_to='speeches/%Y-%m-%d/', max_length=255, blank=True)
    text = models.TextField(blank=True, db_index=False, help_text=_('The text of the speech'))

    # The section that this speech is part of
    section = models.ForeignKey(Section, blank=True, null=True, on_delete=models.SET_NULL,
            help_text=('The section that this speech is contained in'),)
    title = models.TextField(blank=True, help_text=_('The title of the speech, if relevant'))
    # The below two fields could be on the section if we made it a required field of a speech
    event = models.TextField(db_index=True, blank=True, help_text=_('Was the speech at a particular event?'))
    location = models.TextField(db_index=True, blank=True, help_text=_('Where the speech took place'))

    # Metadata on the speech
    # type = models.ChoiceField() # speech, scene, narrative, summary, etc.
    speaker = models.ForeignKey(Speaker, blank=True, null=True, help_text=_('Who gave this speech?'), on_delete=models.SET_NULL)
    # may be null, in which case we simply use current strategy to get name
    speaker_display = models.CharField(max_length=256, null=True, blank=True)

    start_date = models.DateField(blank=True, null=True, help_text=_('What date did the speech start?'))
    start_time = models.TimeField(blank=True, null=True, help_text=_('What time did the speech start?'))
    end_date = models.DateField(blank=True, null=True, help_text=_('What date did the speech end?'))
    end_time = models.TimeField(blank=True, null=True, help_text=_('What time did the speech end?'))
    tags = models.ManyToManyField(Tag, blank=True, null=True)

    public = models.BooleanField(default=True, help_text=_('Is this speech public?'))

    # What if source material has multiple speeches, same timestamp - need a way of ordering them?
    # pos = models.IntegerField()

    source_url = models.TextField(blank=True)
    # source_column? Any other source based things?

    # Task id for celery transcription tasks
    celery_task_id = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'speeches'
        ordering = ( 'start_date', 'start_time', 'id' )

    def __unicode__(self):
        out = 'Speech'
        if self.title: out += ', %s,' % self.title
        if self.speaker: out += ' by %s' % self.speaker
        if self.start_date: out += ' at %s' % self.start_date
        if self.text: out += ' (with text)'
        if self.audio: out += ' (with audio)'
        return out

    @querymethod
    def visible(query, request=None):
        if not request.is_user_instance:
            query = query.filter(public=True)
        return query

    @property
    def is_public(self):
        return self.public

    @property
    def summary(self):
        summary_length = getattr(settings, 'SPEECH_SUMMARY_LENGTH', 30)
        if self.audio and not self.text:
            return "[ recorded audio ]"
        else:
            text = strip_tags(self.text)
            return text[:summary_length] + '...' if len(text) > summary_length else text

    @property
    def start_datetime(self):
        if self.start_date:
            return datetime.datetime.combine(self.start_date, self.start_time or datetime.time(0,0))
        else:
            return None

    @property
    def end_datetime(self):
        if self.end_date:
            return datetime.datetime.combine(self.end_date, self.end_time or datetime.time(0,0))
        else:
            return None

    @models.permalink
    def get_absolute_url(self):
        return ( 'speeches:speech-view', (), { 'pk': self.id } )

    @models.permalink
    def get_edit_url(self):
        return ( 'speeches:speech-edit', (), { 'pk': self.id } )

    @models.permalink
    def get_delete_url(self):
        return ( 'speeches:speech-delete', (), { 'pk': self.id } )

    def get_next_speech(self):
        """Return the next speech to this one in the same section, in a start
        date/time/ID ordering."""
        if self.start_date:
            # A later date, or no date present
            q1 = Q(start_date__gt=self.start_date) | Q(start_date__isnull=True)
            # Or, if on the same date...
            q2 = Q(start_date=self.start_date)
        else:
            # No dates later than our unknown
            q1 = Q()
            # But in that case...
            q2 = Q(start_date__isnull=True)
        if self.start_time:
            # If the time is later, or not present, or the same with a greater ID
            q3 = Q(start_time__gt=self.start_time) | Q(start_time__isnull=True) | Q(start_time=self.start_time, id__gt=self.id)
        else:
            # If the time is not present and the ID is greater
            q3 = Q(start_time__isnull=True, id__gt=self.id)
        q = q1 | ( q2 & q3 )

        if self.section:
            s = list(Speech.objects.filter(q, section=self.section)[:1])
        else:
            s = list(Speech.objects.filter(q, instance=self.instance, section__isnull=True)[:1])
        if s: return s[0]
        if self.section:
            next_section = self.section.get_next_node()
            if next_section:
                s = next_section.speech_set.all()[:1]
        return s and s[0] or None

    def get_previous_speech(self):
        """Return the previous speech to this one in the same section,
        in a start date/time/ID ordering."""
        if self.start_date:
            # A date less than ours
            q1 = Q(start_date__lt=self.start_date)
            # Or if the same date...
            q2 = Q(start_date=self.start_date)
        else:
            # Any speech with a date is earlier
            q1 = Q(start_date__isnull=False)
            # And for those other speeches with no date...
            q2 = Q(start_date__isnull=True)
        if self.start_time:
            # If the time is earlier, or the same and the ID is smaller
            q3 = Q(start_time__lt=self.start_time) | Q(start_time=self.start_time, id__lt=self.id)
        else:
            # If there is a time, or there isn't but the ID is smaller
            q3 = Q(start_time__isnull=False) | Q(start_time__isnull=True, id__lt=self.id)
        q = q1 | ( q2 & q3 )

        if self.section:
            s = list(Speech.objects.filter(q, section=self.section).reverse()[:1])
        else:
            s = list(Speech.objects.filter(q, instance=self.instance, section__isnull=True).reverse()[:1])
        if s: return s[0]
        if self.section:
            prev_section = self.section.get_previous_node()
            if prev_section:
                s = prev_section.speech_set.all().reverse()[:1]
        return s and s[0] or None

    def start_transcribing(self):
        """In the past, kicked off a celery task to transcribe this speech"""
        return

# A timestamp of a particular speaker at a particular time.
# Used to record events like "This speaker started speaking at 00:33"
# in a specific recording, before it's chopped up into a speech
class RecordingTimestamp(InstanceMixin, AuditedModel):
    speaker = models.ForeignKey(Speaker, blank=True, null=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(db_index=True, blank=False)
    speech = models.ForeignKey(Speech, blank=True, null=True, on_delete=models.SET_NULL)
    recording = models.ForeignKey('Recording',blank=False, null=False, related_name='timestamps', default=0) # kludge default 0, should not be used

    class Meta:
        ordering = ('timestamp',)

    @property
    def utc(self):
        """Return our timestamp as a UTC long"""
        return calendar.timegm(self.timestamp.timetuple())


# A raw recording, might be divided up into multiple speeches
class Recording(InstanceMixin, AudioMP3Mixin, AuditedModel):
    audio = models.FileField(upload_to='recordings/%Y-%m-%d/', max_length=255, blank=False)
    start_datetime = models.DateTimeField(blank=True, null=True, help_text='Datetime of first timestamp associated with recording')
    audio_duration = models.IntegerField(blank=True, null=False, default=0, help_text='Duration of recording, in seconds')

    def save(self, *args, **kwargs):
        kwargs['duration'] = True
        super(Recording, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'Recording made %s ago' % timesince(self.created)

    @models.permalink
    def get_absolute_url(self):
        return ( 'speeches:recording-view', (), { 'pk': self.id } )

    def add_speeches_to_section(self, section):
        return Speech.objects.filter(recordingtimestamp__recording=self).update(section=section)

    def create_or_update_speeches(self, instance):
        created_speeches = []

        # Split the recording's audio files
        audio_helper = AudioHelper()
        audio_files = audio_helper.split_recording(self)
        sorted_timestamps = self.timestamps.order_by("timestamp")

        for index, audio_file in enumerate(audio_files):
            new = True
            speech = Speech(
                instance = instance,
                public = False,
            )
            timestamp = None
            if sorted_timestamps and len(sorted_timestamps) > 0:
                # We assume that the files are returned in order of timestamp
                timestamp = sorted_timestamps[index]
                if timestamp.speech:
                    speech = timestamp.speech
                    new = False
                    try:
                        speech.audio.delete(save=False)
                    except:
                        pass
                        # shouldn't happen, but we're going to recreate anyway
                        # so not critical

                speech.speaker = timestamp.speaker
                speech.start_date = timestamp.timestamp.date()
                speech.start_time = timestamp.timestamp.time()
                # If there's another one we can work out the end too
                if index < len(sorted_timestamps) - 1:
                    next_timestamp = sorted_timestamps[index + 1]
                    speech.end_date = next_timestamp.timestamp.date()
                    speech.end_time = next_timestamp.timestamp.time()

            audio_file = open(audio_file, 'rb')
            speech.audio = File(audio_file)
            speech.save()

            if new:
                created_speeches.append( speech )
                if timestamp:
                    timestamp.speech = speech
                    timestamp.save()

        return created_speeches
