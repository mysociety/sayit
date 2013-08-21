import os
import urllib

from speeches.management.import_commands import ImportCommand
from speeches.import_akomantoso import ImportAkomaNtoso

class Command(ImportCommand):
    importer_class = ImportAkomaNtoso


        
