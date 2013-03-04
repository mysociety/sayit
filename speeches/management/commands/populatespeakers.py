import logging
from optparse import make_option

from django.core.management.base import NoArgsCommand
from popit import PopIt
from speeches.models import Speaker
from instances.models import Instance

logger = logging.getLogger(__name__)

class Command(NoArgsCommand):

    help = 'Populates the database with people from Popit'

    option_list = NoArgsCommand.option_list + (
        make_option('--instance', help='Which Sayit instance to add to'),
        make_option('--popit-instance', help='Popit instance name'),
        make_option('--popit-hostname', help='Popit host name'),
        make_option('--popit-version', help='Popit API version'),
    )

    def handle_noargs(self, **options):
        instance = Instance.objects.get(label=options['instance'])

        api = PopIt(instance = options['popit_instance'],
                    hostname = options['popit_hostname'],
                    api_version = options['popit_version'])
        results = api.person.get()
        for person in results['results']:

            logger.info('Processing: {0}'.format(person['meta']['api_url']))

            speaker, created = Speaker.objects.get_or_create(popit_url=person['meta']['api_url'], instance=instance)

            logger.info('Person was created? {0}'.format(created))
            logger.info('Person ID in the database is: {0}'.format(speaker.id))

            # we ignore created for now, just always set the name
            speaker.name = person['name']
            speaker.save()
