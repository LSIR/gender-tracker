from django.test import TestCase
from backend.models import Article, UserLabel
from backend.task_loading import load_hardest_articles, request_labelling_task
from backend.task_parsing import add_user_labels_to_db, add_article_to_db
import spacy
import random


class ArticleTestCase(TestCase):
    # Load the language model
    nlp = spacy.load('fr_core_news_md')

    def setUp(self):
        # Add the articles to the database
        a1 = add_article_to_db('../data/article01.xml', self.nlp)
        a2 = add_article_to_db('../data/article02clean.xml', self.nlp)
        a3 = add_article_to_db('../data/article03clean.xml', self.nlp)

        # Default values
        session_id = 1111
        labels = [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        # Add a user label for article 1
        add_user_labels_to_db(a1.id, session_id, labels, 7, [66])

    def test_load_hardest_articles(self):
        """Checks that the method to extract the hardest articles to predict works"""
        # Generate new confidence numbers, between 0 and 10000
        # (It will be between 0 and 100 in reality but more variance is needed here)
        confidences = []
        for (i, a) in enumerate(Article.objects.all()):
            old_confidences = a.confidence['confidence']
            new_confidences = [random.randint(0, 10000) for _ in old_confidences]
            min_confidence = min(new_confidences)
            a.confidence = {'confidence': new_confidences, 'min_confidence': min_confidence}
            a.save()
            confidences.append(min_confidence)

        confidences.sort(key=lambda x: x)
        confidences = confidences[:2]

        for i, a in enumerate(load_hardest_articles(2)):
            min_conf = a.confidence['min_confidence']
            self.assertEquals(min_conf, confidences[i])
