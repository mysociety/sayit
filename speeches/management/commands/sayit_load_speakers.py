from django.core.management.base import BaseCommand, CommandError

from instances.models import Instance
from speeches.importers.import_popolo import PopoloImporter


class Command(BaseCommand):
    args = '<base-url instance-label>'
    help = 'Imports people, memberships and organizations in Popolo format'

    def handle(self, *args, **options):
        if not args:
            raise CommandError('Please specify a source URL or file')

        base_url = args[0]

        if len(args) == 2:
            instance_label = args[1]
            try:
                instance = Instance.objects.get(label=instance_label)
            except Instance.DoesNotExist:
                raise CommandError(
                    'There is no instance with label %s' % instance_label)
        else:
            instance = None

        if len(args) > 2:
            raise CommandError('Too many arguments: %s' % repr(args))

        importer = PopoloImporter(base_url, instance=instance)
        importer.import_all()
