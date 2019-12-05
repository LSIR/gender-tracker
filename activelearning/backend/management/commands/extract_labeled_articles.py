from django.core.management.base import BaseCommand, CommandError

from backend.xml_parsing import database_to_xml


class Command(BaseCommand):
    help = 'Extracts all labeled articles from the database as XML files'

    def add_arguments(self, parser):
        parser.add_argument('path', help="Path to an empty directory where the articles should be stored.")

    def handle(self, *args, **options):
        path = options['path']
        try:
            database_to_xml(path, 1, 0)
        except IOError:
            raise CommandError('Articles could not be extracted. IO Error.')
