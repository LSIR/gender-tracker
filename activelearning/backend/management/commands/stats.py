from functools import reduce

from django.core.management.base import BaseCommand

from backend.models import Article
from backend.helpers import aggregate_label


class Command(BaseCommand):
    help = 'Displays the number of fully labeled articles and sentences.'

    def handle(self, *args, **options):
        # Number of labeled articles for each source
        labeled_articles = {'Heidi.News': 0, 'Parisien': 0, 'Republique': 0}
        # Number of labeled sentences for each source
        labeled_sentences = {'Heidi.News': 0, 'Parisien': 0, 'Republique': 0}
        # Number of labeled sentences that are quotes for each source
        labeled_quotes = {'Heidi.News': 0, 'Parisien': 0, 'Republique': 0}

        articles = Article.objects.all()
        for a in articles:
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
                                                             labeled_articles[source],
                                                             labeled_sentences[source],
                                                             labeled_quotes[source]))
        total_articles = reduce(lambda x, y: x + y, labeled_articles.values())
        total_sentences = reduce(lambda x, y: x + y, labeled_sentences.values())
        total_quotes = reduce(lambda x, y: x + y, labeled_quotes.values())
        print('{:^20} | {:^20} | {:^20} | {:^20}'.format('Total', total_articles, total_sentences, total_quotes))
        print('\n')
