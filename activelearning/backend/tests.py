from django.test import TestCase
from backend.models import Article, UserLabel
from backend.helpers import add_article_to_db, add_user_labels_to_db, load_hardest_articles
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

        # Add a user label for article 1
        article_id = a1.id
        session_id = 1234
        labels = [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # 8th sentence in the article
        sentence_index = 7
        # 2th paragraph in the article
        author_index = [65, 66, 68]
        add_user_labels_to_db(article_id, session_id, labels, sentence_index, author_index)

    def test_articles_correctly_stored(self):
        """Checks that the Articles are correctly added to the database"""
        articles = Article.objects.all().values('id', 'paragraphs')
        for a in articles:
            print('Articles: ', a)

    def test_labels_correctly_stored(self):
        """Checks that the Labels are correctly added to the database"""
        labels = UserLabel.objects.all()
        for label in labels:
            article = label.article
            label_counts = article.label_counts['label_counts']
            # "border" printed as well
            print('Labels: ', label)
            print(label_counts[99 - 1:129 + 1])

    def test_load_hardest_articles(self):
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
