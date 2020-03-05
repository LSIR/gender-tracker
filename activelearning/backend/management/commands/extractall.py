from django.core.management.base import BaseCommand, CommandError

from backend.helpers import aggregate_label
from backend.models import Article
from backend.xml_parsing.postgre_to_xml import database_to_xml


class Command(BaseCommand):
    help = 'Extracts all labeled articles from the database as XML files'

    def add_arguments(self, parser):
        parser.add_argument('path', help="Path to an empty directory where the articles should be stored.")

    def handle(self, *args, **options):
        path = options['path']
        try:
            articles = Article.objects.all()
            for a in articles:
                if a.labeled['fully_labeled'] == 1:
                    labels = []
                    authors = []
                    for s_id in range(len(a.sentences['sentences'])):
                        sent_label, sent_authors, consensus = aggregate_label(a, s_id)
                        labels.append(sent_label)
                        authors.append(sent_authors)
                    output_xml = database_to_xml(a, labels, authors)
                    with open(f'{path}/article_{a.id}.xml', 'w') as f:
                        f.write(output_xml)

        except IOError:
            raise CommandError('Articles could not be extracted. IO Error.')
