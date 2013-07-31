import os
from optparse import make_option
import urllib
import xml.etree.ElementTree as etree

from django.core.management.base import BaseCommand, CommandError

from speeches.models import Section, Speech, Speaker
from instances.models import Instance
from speeches.import_akomantoso import ImportAkomaNtoso

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--commit', action='store_true', help='Whether to commit to the database or not'),
        make_option('--instance', action='store', default='default', help='Label of instance to add data to'),
        make_option('--file', action='store', help='XML akomantoso document to import'),
        make_option('--dir',  action='store', help='directory of XML akomantoso documents to import'),
    )

    def handle(self, *args, **options):

        if options['file']:
            (section, speakers_matched, speakers_count) = self.import_document(options['file'], **options)
            if section and section.id:
                self.stdout.write("Imported section %d\n\n" % section.id)
            self.stdout.write("    % 3d matched\n" % speakers_matched)
            self.stdout.write(" of % 3d persons\n" % speakers_count)
        elif options['dir']:
            dir = options['dir']
            files = [ os.path.join(root, filename) 
                    for (root, _, files)
                    in os.walk(dir)
                    for filename in files
                    if filename[-4:] == '.xml']
            if not len(files):
                raise CommandError("No xml files found in directory")
            imports = [self.import_document(f, **options) for f in files]
            if options['commit']:
                sections = [a for a,_,_ in imports]
                self.stdout.write("Imported sections %s\n\n" % str(sections))

            (speakers_matched, speakers_count) = reduce(
                lambda (m1,c1), (m2,c2): (m1+m2, c1+c2), imports)
            self.stdout.write("    % 5d matched\n" % speakers_matched)
            self.stdout.write(" of % 5d persons\n" % speakers_count)
        else:
            self.stdout.write( self.help )

    def import_document(self, path, **options):

        if not os.path.isfile(path):
            raise CommandError("No document found")

        try:
            instance = Instance.objects.get(label=options['instance'])
        except:
            raise CommandError("Instance specified not found")

        self.stdout.write("Starting import: %s\n" % path)

        an = ImportAkomaNtoso(instance = instance, commit = options['commit'])
        section = an.import_xml(path)

        self.stdout.write('%d / %d\n' % (an.speakers_matched, an.speakers_count))

        return (section, an.speakers_matched, an.speakers_count)

        
