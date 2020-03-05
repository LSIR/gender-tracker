from os import listdir
from os.path import isfile, join

from django.core.management.base import BaseCommand, CommandError

from backend.db_management import add_article_to_db
from backend.xml_parsing.helpers import load_nlp


class Command(BaseCommand):
    help = 'Adds a new article to the database'

    def add_arguments(self, parser):
        parser.add_argument('path', help="Path of the article to add to the database")
        parser.add_argument('--source', required=True, choices=['Heidi.News', 'Parisien', 'Republique'],
                            help="The newspaper in which the articles were published")

    def handle(self, *args, **options):
        path = options['path']
        source = 'None'
        if options['source']:
            source = options['source']
        print(f'Loading data from: {path}')
        try:
            articles = []
            article_files = [join(path, article) for article in listdir(path)
                             if isfile(join(path, article)) and len(article) > 4 and article[-3:] == 'xml']
            article_files.sort()
            print('Loading language model...')
            nlp = load_nlp()
            print('Adding articles to the database...')
            for article_path in article_files:
                articles.append(add_article_to_db(article_path, nlp, source))
        except IOError:
            raise CommandError('Article could not be added. IOError.')

        self.stdout.write(self.style.SUCCESS(f'Successfully added {len(articles)} article(s).'))
