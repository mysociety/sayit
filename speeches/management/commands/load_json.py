import os
import urllib

from speeches.management.import_commands import ImportCommand
from speeches.importers.import_json import ImportJson
from optparse import make_option

class Command(ImportCommand):
    importer_class = ImportJson
    document_extension = 'txt'

    option_list = ImportCommand.option_list + (
        make_option('--toplevel',  action='store', default=None, help='Top level section to import into'),
        make_option('--category_field',  action='store', default=None, help='Field name to take mid-level section name from'),
    )
