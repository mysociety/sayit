import logging
from django.core.management.base import NoArgsCommand
from django.conf import settings
from popit import PopIt
from speeches.models import Speaker

logger = logging.getLogger(__name__)

class Command(NoArgsCommand):

    help = 'Populates the database with people from Popit'

    def handle_noargs(self, **options):
        api = PopIt(instance = settings.POPIT_INSTANCE,
                    hostname = settings.POPIT_HOSTNAME,
                    api_version = settings.POPIT_API_VERSION)
        results = api.person.get()
        for person in results['results']:

            logger.info('Processing: {0}'.format(person['meta']['api_url']))

            speaker, created = Speaker.objects.get_or_create(popit_url=person['meta']['api_url'])

            logger.info('Person was created? {0}'.format(created))
            logger.info('Persons id in the spoke db is: {0}'.format(speaker.id))

            # we ignore created for now, just always set the name
            speaker.name = person['name']
            speaker.save();
