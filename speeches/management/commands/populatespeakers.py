import logging
from optparse import make_option

from django.core.management.base import NoArgsCommand
from popit import PopIt
from speeches.models import Speaker

logger = logging.getLogger(__name__)

class Command(NoArgsCommand):

    help = 'Populates the database with people from Popit'

    option_list = NoArgsCommand.option_list + (
        make_option('--instance', help='Popit instance name'),
        make_option('--hostname', help='Popit host name'),
        make_option('--api-version', help='Popit API version'),
    )

    def handle_noargs(self, **options):
        api = PopIt(instance = options['instance'],
                    hostname = options['hostname'],
                    api_version = options['api_version'])
        results = api.person.get()
        for person in results['results']:

            logger.info('Processing: {0}'.format(person['meta']['api_url']))

            speaker, created = Speaker.objects.get_or_create(popit_url=person['meta']['api_url'])

            logger.info('Person was created? {0}'.format(created))
            logger.info('Person ID in the database is: {0}'.format(speaker.id))

            # we ignore created for now, just always set the name
            speaker.name = person['name']
            speaker.save();
