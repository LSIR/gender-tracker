from django.test import TestCase
from backend.models import Article, UserLabel
from backend.helpers import add_article_to_db, add_user_labels_to_db, load_hardest_articles, request_labelling_task
import spacy
import random

class ArticleTestCase(TestCase):

    def setUp(self):
        # Load the language model
        nlp = spacy.load('fr_core_news_md')

        # Add the articles to the database
        a1 = add_article_to_db('../data/article01clean.xml', nlp)
        a2 = add_article_to_db('../data/article02clean.xml', nlp)
        # Duplicate Articles to test the load method
        a3 = add_article_to_db('../data/article01clean.xml', nlp)
        a4 = add_article_to_db('../data/article02clean.xml', nlp)

        # Default values
        session_id = 1234
        labels = [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        # Add a user label for article 1: Only one that actually makes sense
        add_user_labels_to_db(a1.id, session_id, labels, 7, [66])

        # Add other user labels
        add_user_labels_to_db(a1.id, session_id, labels, 0, 10 * [0])
        add_user_labels_to_db(a1.id, session_id, labels, 1, 11* [0])
        add_user_labels_to_db(a1.id, session_id, labels, 2, 12 * [0])

        add_user_labels_to_db(a2.id, session_id, labels, 0, 10 * [0])
        add_user_labels_to_db(a2.id, session_id, labels, 1, 11 * [0])
        add_user_labels_to_db(a2.id, session_id, labels, 5, 12 * [0])

        add_user_labels_to_db(a3.id, session_id, labels, 0, 10 * [0])
        add_user_labels_to_db(a3.id, session_id, labels, 1, 11 * [0])
        add_user_labels_to_db(a3.id, session_id, labels, 2, 12 * [0])

        add_user_labels_to_db(a4.id, session_id, labels, 0, 10 * [0])
        add_user_labels_to_db(a4.id, session_id, labels, 1, 11 * [0])
        add_user_labels_to_db(a4.id, session_id, labels, 5, 12 * [0])

    def test_articles_correctly_stored(self):
        print('\n')
        """Checks that the Articles are correctly added to the database"""
        articles = Article.objects.all().values('id', 'paragraphs')
        for a in articles:
            print('Articles: ', a)

    def test_labels_correctly_stored(self):
        print('\n')
        """Checks that the Labels are correctly added to the database"""
        labels = UserLabel.objects.all()
        for label in labels:
            article = label.article
            label_counts = article.label_counts['label_counts']
            print('Labels: ', label)
            print(label_counts[0:11])

    def test_load_hardest_articles(self):
        print('\n')
        """Checks that the method to extract the hardest articles to predict works"""
        # Generate new confidence numbers, between 0 and 10000
        # (It will be between 0 and 100 in reality but more variance is needed here)
        for (i, a) in enumerate(Article.objects.all()):
            old_confidences = a.confidence['confidence']
            new_confidences = [random.randint(0, 10000) for c in old_confidences]
            min_confidence = min(new_confidences)
            a.confidence = {'confidence': new_confidences, 'min_confidence': min_confidence}
            a.save()
            print(f'Article: {a.id}, min confidence = {min_confidence}')

        print('\n\n2 Most difficult articles to classify:')

        for a in load_hardest_articles(2):
            min_conf = a.confidence['min_confidence']
            print(f'Article: {a.id}, min confidence = {min_conf}')

    def test_request_labelling_task(self):
        """Checks that the method to extract the hardest articles to predict works"""
        # Generate new confidence numbers, between 0 and 10000
        # (It will be between 0 and 100 in reality but more variance is needed here)
        print('\n')
        print(f"First task: {request_labelling_task(1234)}")
        print(f"Second task: {request_labelling_task(9999)}")
