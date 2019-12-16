from django.core.management.base import BaseCommand, CommandError

from backend.task_parsing import add_article_to_db

from os import listdir
from os.path import isfile,join

import spacy


class Command(BaseCommand):
    help = 'Adds a new article to the database'

    def add_arguments(self, parser):
        parser.add_argument('path', help="Path of the article to add to the database")
        parser.add_argument('--dir', action='store_true', help="Adds all xml files in the directory to the database")

    def handle(self, *args, **options):
        path = options['path']
        print(f'Loading data from: {path}')
        try:
            if options['dir']:
                articles = []
                article_files = [join(path, article) for article in listdir(path)
                                 if isfile(join(path, article)) and len(article) > 4 and article[-3:] == 'xml']
                print('Loading language model...')
                nlp = spacy.load('fr_core_news_md')
                for article_path in article_files:
                    articles.append(add_article_to_db(article_path, nlp))
            else:
                print('Loading language model...')
                nlp = spacy.load('fr_core_news_md')
                articles = [add_article_to_db(path, nlp)]
        except IOError:
            raise CommandError('Article could not be added. IOError.')

        self.stdout.write(self.style.SUCCESS(f'Successfully added {len(articles)} article(s).'))
