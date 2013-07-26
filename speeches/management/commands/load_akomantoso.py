import os
from optparse import make_option
import urllib
import xml.etree.ElementTree as etree

from django.core.management.base import BaseCommand, CommandError

from speeches.models import Section, Speech, Speaker
from instances.models import Instance
from speeches.import_akomantoso import ImportAkomaNtoso

class Command(BaseCommand):
    args = '<path>'
    help = 'Import an akomantoso document into a SayIt instance'
    option_list = BaseCommand.option_list + (
        make_option('--commit', action='store_true', help='Whether to commit to the database or not'),
        make_option('--instance', action='store', default='default', help='Label of instance to add data to'),
    )

    def handle(self, *args, **options):

        path = args[0]

        if not os.path.isfile(path):
            raise CommandError("No document found")

        try:
            instance = Instance.objects.get(label=options['instance'])
        except:
            raise CommandError("Instance specified not found")

        self.stdout.write("Starting import!\n\n")

        an = ImportAkomaNtoso(instance = instance, commit = options['commit'])
        section = an.import_xml(path)

        if section and section.id:
            self.stdout.write("Imported section %d\n\n" % section.id)

        self.stdout.write("    % 3d matched\n" % an.speakers_matched)
        self.stdout.write(" of % 3d persons\n" % an.speakers_count)



        
