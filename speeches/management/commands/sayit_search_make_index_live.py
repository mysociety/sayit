from django.utils.translation import ugettext_lazy as _
from django.core.management.base import BaseCommand
from django.conf import settings

from haystack.utils import loading


class Command(BaseCommand):
    help = _('Update the default alias to point at search index write alias is using')

    def handle(self, *args, **options):
        connection_options = settings.HAYSTACK_CONNECTIONS['default']

        index_name = connection_options['INDEX_NAME']
        index_write = '%s_write' % index_name

        BackendClass = loading.import_class(connection_options['ENGINE']).backend
        backend = BackendClass('default', **connection_options)

        actions = []
        current_alias = None
        for n, al in backend.conn.aliases().items():
            if index_name in al['aliases']:
                actions.append({'remove': {'index': n, 'alias': index_name}})
            if index_write in al['aliases']:
                current_alias = n

        if not current_alias:
            raise Exception('There is no "%s" alias to use' % index_write)

        actions.append({'add': {'index': current_alias, 'alias': index_name}})
        backend.conn.update_aliases({'actions': actions})
