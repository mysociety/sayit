from datetime import datetime

from django.utils.translation import ugettext_lazy as _
from django.core.management.base import BaseCommand
from django.conf import settings

from haystack.utils import loading


class Command(BaseCommand):
    help = _('Create a new dated search index for reindexing with no downtime')

    def handle(self, *args, **options):
        connection_options = settings.HAYSTACK_CONNECTIONS['default']

        index_name = connection_options['INDEX_NAME']
        new_alias = '%s_%s' % (index_name, datetime.now().isoformat().lower())
        connection_options['INDEX_NAME'] = new_alias

        BackendClass = loading.import_class(connection_options['ENGINE']).backend
        backend = BackendClass('default', **connection_options)
        backend.setup()

        index_write = '%s_write' % index_name

        aliases = backend.conn.aliases()
        actions = []
        for n, al in aliases.items():
            if index_write in al['aliases']:
                actions.append({'remove': {'index': n, 'alias': index_write}})

        actions.append({'add': {'index': new_alias, 'alias': index_write}})
        backend.conn.update_aliases({'actions': actions})
