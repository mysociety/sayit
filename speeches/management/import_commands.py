import json
import logging
import os
import traceback
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from instances.models import Instance

logger = logging.getLogger(__name__)


def _stats_pretty(stats):
    return ' '.join(["%s:%d" % (cls.__name__, n) for cls, n in stats.items()])


class ImportCommand(BaseCommand):

    importer_class = None
    document_extension = ''

    option_list = BaseCommand.option_list + (
        make_option('--commit', action='store_true', help='Whether to commit to the database or not'),
        make_option('--instance', action='store', help='Label of instance to add data to'),
        make_option('--file', action='store', help='document to import'),
        make_option('--dir', action='store', help='directory of documents to import'),
        make_option(
            '--no-verify', action='store_false', default=True, dest='verify',
            help='Whether to verify SSL certificates or not'),
        make_option(
            '--start-date', action='store', default='',
            help='earliest date to process, in yyyy-mm-dd format'),
        make_option(
            '--dump-users', action='store', default='',
            help='dump a json list to <file> (only valid with --dir for now)'),
        make_option(
            '--clobber-existing', action='store_const', const='replace', dest='clobber',
            help='Whether to replace sections with the same heading'),
        make_option(
            '--skip-existing', action='store_const', const='skip', dest='clobber',
            help='Whether to skip sections with the same heading'),
        make_option(
            '--merge-existing', action='store_const', const='merge', dest='clobber',
            help='Whether to merge sections with the same heading'),
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
            (stats, speakers) = self.import_document(filename, **options)
            if verbosity > 1 and stats:
                logger.info("Imported %s\n\n" % _stats_pretty(stats))
        elif options['dir']:
            files = sorted(self.document_list(options))

            if len(files):
                speakers = {}
                for f in files:
                    (stats, spkrs) = self.import_document(f, **options)
                    speakers.update(spkrs)

                    if verbosity > 1 and stats:
                        logger.info("%s: Imported %s\n" % (f, _stats_pretty(stats)))

                dump_users = os.path.expanduser(options['dump_users'])
                if dump_users:
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
        if start_date:
            def valid(f):
                return f >= start_date
        else:
            def valid(f):
                return True

        return [os.path.join(root, filename)
                for (root, _, files)
                in os.walk(dir)
                for filename in files
                if filename[-4:] == '.%s' % self.document_extension and valid(filename)]

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
            importer.import_document(path)
        except Exception as e:
            logger.error("An exception of type %s occurred, arguments:\n%s\n%s" % (
                type(e).__name__, e, traceback.format_exc()))
            return (None, {})

        return (importer.stats, importer.speakers)
