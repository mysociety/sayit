from datetime import datetime

import pyelasticsearch

from django.core.management.base import BaseCommand
from django.conf import settings

from spoke.search.backends import SayitElasticBackend

class Command(BaseCommand):
    help = 'Create a new dated search index for reindexing with no downtime'

    def handle(self, *args, **options):
        connection_options = settings.HAYSTACK_CONNECTIONS['default']

        index_name = connection_options['INDEX_NAME']
        new_alias = '%s_%s' % (index_name, datetime.now().isoformat().lower())
        connection_options['INDEX_NAME'] = new_alias

        backend = SayitElasticBackend('default', **connection_options)
        backend.setup()

        index_write = '%s_write' % index_name

        aliases = backend.conn.aliases()
        actions = []
        for n, al in aliases.items():
            if index_write in al['aliases']:
                actions.append( { 'remove': { 'index': n, 'alias': index_write } } )

        actions.append( { 'add': { 'index': new_alias, 'alias': index_write } } )
        backend.conn.update_aliases({ 'actions': actions })
