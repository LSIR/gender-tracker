from functools import reduce
from numpy.random import random

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
        # Number of labeled articles for each source
        train_articles = {'Heidi.News': 0, 'Parisien': 0, 'Republique': 0}
        # Number of labeled articles for each source
        test_articles = {'Heidi.News': 0, 'Parisien': 0, 'Republique': 0}
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

                # Check if the article is in the training or test set.
                if 'test_set' not in a.labeled or type(a.labeled['test_set']) is not int:
                    a.labeled['test_set'] = int(random() > 0.9)
                    a.save()
                if a.labeled['test_set'] == 0:
                    train_articles[a.source] += 1
                else:
                    test_articles[a.source] += 1

                # Check if each sentence is a quote or not.
                for sentence_index, end in enumerate(a.sentences['sentences']):
                    labeled_sentences[a.source] += 1
                    # Compute consensus labels
                    sentence_labels, sentence_authors, _ = aggregate_label(a, sentence_index)
                    # If the sentence is a quote, add the number of quotes to the source
                    if sum(sentence_labels) > 0:
                        labeled_quotes[a.source] += 1

        def form_string(base_string, article_source):
            return base_string.format(
                source,
                f'{labeled_articles[article_source]}/{articles_count[article_source]}',
                f'{train_articles[article_source]}/{labeled_articles[article_source]}',
                f'{test_articles[article_source]}/{labeled_articles[article_source]}',
                f'{labeled_sentences[article_source]}/{sentences_count[article_source]}',
                f'{labeled_quotes[article_source]}/?'
            )

        base = '{:^15} | {:^15} | {:^15} | {:^15} | {:^15} | {:^15}'

        print('\n')
        print(base.format('Source', 'Articles', 'Train', 'Test', 'Sentences', 'Quotes'))
        print(f'{110 * "-"}')
        for source in labeled_articles.keys():
            print(form_string(base, source))

        all_articles = reduce(lambda x, y: x + y, articles_count.values())
        labeled_articles = reduce(lambda x, y: x + y, labeled_articles.values())
        training_articles = reduce(lambda x, y: x + y, train_articles.values())
        testing_articles = reduce(lambda x, y: x + y, test_articles.values())
        all_sentences = reduce(lambda x, y: x + y, sentences_count.values())
        labeled_sentences = reduce(lambda x, y: x + y, labeled_sentences.values())
        all_quotes = reduce(lambda x, y: x + y, labeled_quotes.values())
        print(base.format('', '', '', '', '', ''))
        print(base.format('Total', f'{labeled_articles}/{all_articles}', f'{training_articles}/{labeled_articles}',
                          f'{testing_articles}/{labeled_articles}', f'{labeled_sentences}/{all_sentences}',
                          f'{all_quotes}/?'))
        print('\n')
