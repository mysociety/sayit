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
        for person in results['results']:
            speaker, created = Speaker.objects.get_or_create(popit_id=person['_id'])
            # we ignore created for now, just always set the name
            speaker.name = person['name']
            speaker.save();
