import os
import urllib

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from speeches.models import Speech, Speaker
from instances.models import Instance
from popit_resolver.resolve import ResolvePopitName
import datetime

class Command(BaseCommand):

    help = "Rerun popit-resolver resolution, based on the current index of names available.  \nYou will first need to have run popit_resolver_init to set up the names to match against"

    option_list = BaseCommand.option_list + (

        make_option('--instance', action='store', default='default', help='Label of instance to re-resolve'),
        make_option('--name-startswith', action='store', help='name startswith clause for speaker name (not speech display name)'),
        # make_option('--redo', action='store-true', help='refresh already resolved names'),
    )


    def handle(self, *args, **options):
        instance = options['instance']

        reparented_count = 0
        updated_count = 0

        # TODO get verbose from option
        VERBOSE = 2

        speakers = Speaker.objects.filter(person=None)
        if options['name_startswith']:
            speakers = speakers.filter(name__startswith = options['name_startswith'])

        for speaker in speakers:

            if speaker.name == '(narrative)':
                continue

            speeches = speaker.speech_set
            cache = {} # name to speaker
            keep = False

            if VERBOSE >= 1:
                self.stdout.write('Processing speaker %s (%d)\n' % (speaker.name, speaker.id))

            for speech in speeches.all():
                name = speech.speaker_display or speaker.name

                if VERBOSE > 1:
                    self.stdout.write('- %s\n' % name)

                # return cached if relevant
                if name in cache:
                    cached_speaker = cache[name]
                    if not cached_speaker:
                        if VERBOSE > 1:
                            self.stdout.write('   (not resolved, skipping)\n')
                        continue

                    speech.speaker = cached_speaker
                    speech.save()
                    reparented_count += 1
                    if VERBOSE > 1:
                        self.stdout.write('  (from cache %d)\n' % cached_speaker.id)
                    continue

                resolver = ResolvePopitName(
                    date = speech.start_date or datetime.date.today() )
                person = resolver.get_person(name)
                if not person:
                    if VERBOSE > 1:
                        self.stdout.write('  (NO PERSON FOUND)\n')
                        cache[name] = None
                    continue

                self.stdout.write('  (found person %s)\n' % person.popit_id)

                existing_speakers = Speaker.objects.filter(person=person)
                if existing_speakers.count():
                    # assume there is just one (or that the first one is good) for now
                    existing_speaker = existing_speakers[0]
                    cache[name] = existing_speaker
                    speech.speaker = existing_speaker
                    speech.save()
                    reparented_count += 1
                    if VERBOSE > 1:
                        self.stdout.write('  (found existing speaker %d)\n' % existing_speaker.id)
                else:
                    # we will update this speaker to point at the popit person
                    keep = True # e.g. don't delete this speaker (TODO)
                    speaker.person = person
                    speaker.save()
                    updated_count += 1
                    if VERBOSE > 1:
                        self.stdout.write('  (updated speaker)\n')
                    break
        if VERBOSE >= 1:
            self.stdout.write('-----\n')
            self.stdout.write('Reparented: %d\n' % reparented_count)
            self.stdout.write('Updated:    %d\n' % updated_count)

