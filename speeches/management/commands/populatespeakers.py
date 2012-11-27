from django.core.management.base import NoArgsCommand
from django.conf import settings
from popit import PopIt
from speeches.models import Speaker

class Command(NoArgsCommand):
    help = 'Populates the database with people from Popit'

    def handle_noargs(self, **options):
        api = PopIt(instance = settings.POPIT_INSTANCE,
                    hostname = settings.POPIT_HOSTNAME,
                    api_version = settings.POPIT_API_VERSION)
        results = api.person.get()
        for person in results['results']:
            speaker, created = Speaker.objects.get_or_create(popit_id=person['_id'])
            # we ignore created for now, just always set the name
            speaker.name = person['name']
            speaker.save();
