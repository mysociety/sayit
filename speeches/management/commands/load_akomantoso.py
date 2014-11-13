from speeches.management.import_commands import ImportCommand
from speeches.importers.import_akomantoso import ImportAkomaNtoso


class Command(ImportCommand):
    importer_class = ImportAkomaNtoso
    document_extension = 'xml'
