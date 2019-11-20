from django.core.management.base import BaseCommand, CommandError
from backend.helpers import add_article_to_db
import spacy


class Command(BaseCommand):
    help = 'Adds a new article to the database'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs=1, help="Path of the article to add to the database")

    def handle(self, *args, **options):
        path = options['path']
        nlp = spacy.load('fr_core_news_md')
        try:
            article = add_article_to_db(path, nlp)
        except IOError:
            raise CommandError('Article could not be added')

        self.stdout.write(self.style.SUCCESS(f'Successfully added article {article.id}'))
