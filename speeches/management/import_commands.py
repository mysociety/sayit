import os
from optparse import make_option
import urllib

from django.core.management.base import BaseCommand, CommandError

from speeches.models import Section, Speech, Speaker
from instances.models import Instance

class ImportCommand(BaseCommand):

    importer_class = None

    option_list = BaseCommand.option_list + (
        make_option('--commit', action='store_true', help='Whether to commit to the database or not'),
        make_option('--instance', action='store', default='default', help='Label of instance to add data to'),
        make_option('--file', action='store', help='document to import'),
        make_option('--dir',  action='store', help='directory of documents to import'),
        make_option('--start-date',  action='store', default='', help='earliest date to process, in yyyy-mm-dd format'),
        make_option('--dump-users',  action='store', default='', help='dump a json list to <file> (only valid with --dir for now)'),
    )

    def handle(self, *args, **options):

        if options['file']:
            (section, speakers_matched, speakers_count, speakers) = self.import_document(options['file'], **options)
            if section and section.id:
                self.stdout.write("Imported section %d\n\n" % section.id)
            self.stdout.write("    % 3d matched\n" % speakers_matched)
            self.stdout.write(" of % 3d persons\n" % speakers_count)
        elif options['dir']:
            dir = options['dir']

            start_date = options['start_date']
            valid = lambda f: f > start_date if start_date else lambda _: True

            files = [ os.path.join(root, filename) 
                    for (root, _, files)
                    in os.walk(dir)
                    for filename in files
                    if filename[-4:] == '.xml'
                    and valid(filename)]

            if not len(files):
                raise CommandError("No xml files found in directory")

            imports = [self.import_document(f, **options) for f in files]

            if options['commit']:
                sections = [a for a,_,_ in imports]
                self.stdout.write("Imported sections %s\n\n" % str(sections))

            (_, speakers_matched, speakers_count, _) = reduce(
                lambda (s1,m1,c1,d1), (s2,m2,c2,d2): (None, m1+m2, c1+c2, None), imports)
            self.stdout.write("    % 5d matched\n" % speakers_matched)
            self.stdout.write(" of % 5d persons\n" % speakers_count)

            dump_users = options['dump_users']
            if dump_users:
                speakers = {}
                for (_,_,_,d) in imports:
                    speakers.update(d)

                out = open(dump_users, 'w')
                speakers_list = [ (k, speakers[k]) for k in speakers]
                out.write( json.dumps( speakers_list, indent=4 ) )

                self.stdout.write("Saved speakers list to %s\n" % dump_users)

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

        if self.importer_class == None:
            raise CommandError("No importer_class specified!")

        importer = self.importer_class(instance = instance, commit = options['commit'])

        try:
            section = importer.import_xml(path)
        except Exception as e:
            self.stderr.write(str(e))
            return (None, 0, 0, {})

        self.stdout.write('%d / %d\n' % (importer.speakers_matched, importer.speakers_count))

        return (section, importer.speakers_matched, importer.speakers_count, importer.speakers)

        
