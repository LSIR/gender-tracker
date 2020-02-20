from functools import reduce

from django.core.management.base import BaseCommand

from backend.models import Article
from backend.helpers import aggregate_label


class Command(BaseCommand):
    help = 'Displays the number of fully labeled articles and sentences.'

    def handle(self, *args, **options):
        # Number of total articles for each source
        articles_count = {'Heidi.News': 0, 'Parisien': 0, 'Republique': 0}
        # Number of labeled articles for each source
        labeled_articles = {'Heidi.News': 0, 'Parisien': 0, 'Republique': 0}
        # Number of labeled sentences for each source
        labeled_sentences = {'Heidi.News': 0, 'Parisien': 0, 'Republique': 0}
        # Number of total sentences for each source
        sentences_count = {'Heidi.News': 0, 'Parisien': 0, 'Republique': 0}
        # Number of labeled sentences that are quotes for each source
        labeled_quotes = {'Heidi.News': 0, 'Parisien': 0, 'Republique': 0}

        articles = Article.objects.all()
        for a in articles:
            articles_count[a.source] += 1
            sentences_count[a.source] += len(a.sentences['sentences'])
            if a.labeled['fully_labeled'] == 1:
                labeled_articles[a.source] += 1
                for sentence_index, end in enumerate(a.sentences['sentences']):
                    labeled_sentences[a.source] += 1
                    # Compute consensus labels
                    sentence_labels, sentence_authors, _ = aggregate_label(a, sentence_index)
                    # If the sentence is a quote, add the number of quotes to the source
                    if sum(sentence_labels) > 0:
                        labeled_quotes[a.source] += 1

        print('\n{:^20} | {:^20} | {:^20} | {:^20}'.format('Source', 'Articles', 'Sentences', 'Quotes'))
        print(f'{90 * "-"}')
        for source in labeled_articles.keys():
            print('{:^20} | {:^20} | {:^20} | {:^20}'.format(source,
                                                             f'{labeled_articles[source]}/{articles_count[source]}',
                                                             f'{labeled_sentences[source]}/{sentences_count[source]}',
                                                             f'{labeled_quotes[source]}/?'))
        all_articles = reduce(lambda x, y: x + y, articles_count.values())
        labeled_articles = reduce(lambda x, y: x + y, labeled_articles.values())
        all_sentences = reduce(lambda x, y: x + y, sentences_count.values())
        labeled_sentences = reduce(lambda x, y: x + y, labeled_sentences.values())
        all_quotes = reduce(lambda x, y: x + y, labeled_quotes.values())
        print('{:^20} | {:^20} | {:^20} | {:^20}'.format('', '', '', ''))
        print('{:^20} | {:^20} | {:^20} | {:^20}'.format('Total',
                                                         f'{labeled_articles}/{all_articles}',
                                                         f'{labeled_sentences}/{all_sentences}',
                                                         f'{all_quotes}/?'))
        print('\n')
