import json
import logging
import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from instances.models import Instance

logger = logging.getLogger(__name__)


class ImportCommand(BaseCommand):

    importer_class = None
    document_extension = ''

    option_list = BaseCommand.option_list + (
        make_option('--commit', action='store_true', help='Whether to commit to the database or not'),
        make_option('--instance', action='store', help='Label of instance to add data to'),
        make_option('--file', action='store', help='document to import'),
        make_option('--dir', action='store', help='directory of documents to import'),
        make_option(
            '--start-date', action='store', default='',
            help='earliest date to process, in yyyy-mm-dd format'),
        make_option(
            '--dump-users', action='store', default='',
            help='dump a json list to <file> (only valid with --dir for now)'),
        make_option(
            '--clobber-existing', action='store_true', dest='clobber',
            help='Whether to replace top-level sections with the same heading'),
        make_option(
            '--skip-existing', action='store_false', dest='clobber',
            help='Whether to skip top-level sections with the same heading'),
    )

    def handle(self, *args, **options):
        verbosity = int(options['verbosity'])

        if options['commit']:
            if not options['instance']:
                raise CommandError("You must specify an instance")
            instance, __ = Instance.objects.get_or_create(label=options['instance'])
        else:
            instance = Instance(label=options['instance'])
        options['instance'] = instance

        if options['file']:
            filename = os.path.expanduser(options['file'])
            (section, speakers) = self.import_document(filename, **options)
            if verbosity > 1:
                if section and section.id:
                    logger.info("Imported section %d\n\n" % section.id)
        elif options['dir']:
            files = self.document_list(options)

            if len(files):
                imports = [self.import_document(f, **options) for f in files]

                if options['commit']:
                    sections = [a for a, _ in imports]
                    if verbosity > 1:
                        logger.info("Imported sections %s\n\n" % str([s.id for s in sections]))

                dump_users = os.path.expanduser(options['dump_users'])
                if dump_users:
                    speakers = {}
                    for (_, d) in imports:
                        speakers.update(d)

                    out = open(dump_users, 'w')
                    speakers_list = [(k, speakers[k]) for k in speakers]
                    out.write(json.dumps(speakers_list, indent=4))

                    if verbosity > 1:
                        logger.info("Saved speakers list to %s\n" % dump_users)
            else:
                logger.info("No .%s files found in directory" % self.document_extension)
        else:
            logger.info(self.help)

    def document_list(self, options):
        dir = os.path.expanduser(options['dir'])

        start_date = options['start_date']
        valid = lambda f: f >= start_date if start_date else lambda _: True

        return [os.path.join(root, filename)
                for (root, _, files)
                in os.walk(dir)
                for filename in files
                if filename[-4:] == '.%s' % self.document_extension
                and valid(filename)]

    def document_valid(self, path):
        return os.path.isfile(path)

    def import_document(self, path, **options):
        verbosity = int(options['verbosity'])

        if not self.document_valid(path):
            raise CommandError("No document found")

        if verbosity > 1:
            logger.info("Starting import: %s\n" % path)

        if self.importer_class is None:
            raise CommandError("No importer_class specified!")

        importer = self.importer_class(**options)

        try:
            section = importer.import_document(path)
        except Exception as e:
            logger.error("An exception of type %s occurred, arguments:\n%s" % (
                type(e).__name__, e))
            return (None, {})

        return (section, importer.speakers)
