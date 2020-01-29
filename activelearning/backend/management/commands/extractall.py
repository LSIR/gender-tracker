from django.core.management.base import BaseCommand, CommandError

from backend.xml_parsing.postgre_to_xml import database_to_xml
from backend.helpers import is_article_labelled, label_consensus
from backend.models import Article, UserLabel


class Command(BaseCommand):
    help = 'Extracts all labeled articles from the database as XML files'

    def add_arguments(self, parser):
        parser.add_argument('path', help="Path to an empty directory where the articles should be stored.")

    def handle(self, *args, **options):
        path = options['path']
        try:
            articles = Article.objects.all()
            for a in articles:
                if is_article_labelled(a, 4, 80):
                    labels = []
                    authors = []
                    for s_id in range(len(a.sentences['sentences'])):
                        sentence_labels = UserLabel.objects.filter(article=a, sentence_index=s_id)
                        all_labels = [label.labels['labels'] for label in sentence_labels]
                        all_authors = [label.author_index['author_index'] for label in sentence_labels]
                        sent_label, sent_authors, consensus = label_consensus(all_labels, all_authors)
                        labels.append(sent_label)
                        authors.append(sent_authors)
                    output_xml = database_to_xml(a, labels, authors)
                    with open(f'{path}/article_{a.id}.xml', 'w') as f:
                        f.write(output_xml)

        except IOError:
            raise CommandError('Articles could not be extracted. IO Error.')
