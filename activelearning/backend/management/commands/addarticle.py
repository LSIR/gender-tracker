from django.core.management.base import BaseCommand, CommandError

from backend.db_management import add_article_to_db

from os import listdir
from os.path import isfile, join

import spacy


def set_custom_boundaries(doc):
    """
    Custom boundaries so that spaCy doesn't split sentences at ';' or at '-[A-Z]'.
    """
    for token in doc[:-1]:
        if token.text == ";":
            doc[token.i+1].is_sent_start = False
        if token.text == "-" and token.i != 0:
            doc[token.i].is_sent_start = False
    return doc


class Command(BaseCommand):
    help = 'Adds a new article to the database'

    def add_arguments(self, parser):
        parser.add_argument('path', help="Path of the article to add to the database")
        parser.add_argument('--source', help="The newspaper in which the articles were published")
        parser.add_argument('--dir', action='store_true', help="Adds all xml files in the directory to the database")

    def handle(self, *args, **options):
        path = options['path']
        source = 'None'
        if options['source']:
            source = options['source']
        print(f'Loading data from: {path}')
        try:
            if options['dir']:
                articles = []
                article_files = [join(path, article) for article in listdir(path)
                                 if isfile(join(path, article)) and len(article) > 4 and article[-3:] == 'xml']
                article_files.sort()
                print('Loading language model...')
                nlp = spacy.load('fr_core_news_md')
                nlp.add_pipe(set_custom_boundaries, before="parser")
                print('Adding articles to the database...')
                for article_path in article_files:
                    articles.append(add_article_to_db(article_path, nlp, source))
            else:
                print('Loading language model...')
                nlp = spacy.load('fr_core_news_md')
                nlp.add_pipe(set_custom_boundaries, before="parser")
                articles = [add_article_to_db(path, nlp, source)]
        except IOError:
            raise CommandError('Article could not be added. IOError.')

        self.stdout.write(self.style.SUCCESS(f'Successfully added {len(articles)} article(s).'))
