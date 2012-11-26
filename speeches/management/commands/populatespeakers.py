from django.core.management.base import NoArgsCommand
import pprint
from popit import PopIt
from speeches.models import Speaker

class Command(NoArgsCommand):
    help = 'Populates the database with people from Popit'

    def handle_noargs(self, **options):
        pp = pprint.PrettyPrinter(indent=4)
        # Do populating
        api = PopIt(instance = 'ukcabinet', hostname = 'ukcabinet.popit.mysociety.org', api_version = 'v1')
        results = api.person.get()
        self.stdout.write('Names will be:\n')
        for person in results['results']:
            self.stdout.write('Processing person: ' + pp.pformat(person) + '\n')
            try:
                speaker = Speaker.objects.get(popit_id=person['_id'])
            except Speaker.DoesNotExist:
                speaker = Speaker()
                speaker.popit_id = person['_id']
            speaker.name = person['name']
            speaker.save();
