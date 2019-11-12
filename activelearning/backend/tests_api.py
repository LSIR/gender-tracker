from django.test import TestCase
from django.test import Client
from backend.models import Article, UserLabel
from backend.helpers import add_article_to_db, add_user_labels_to_db, load_hardest_articles, request_labelling_task
import spacy
import random


class ApiTestCase(TestCase):

    def setUp(self):
        # Load the language model
        nlp = spacy.load('fr_core_news_md')
        # Add the articles to the database
        a1 = add_article_to_db('../data/article01clean.xml', nlp)
        a2 = add_article_to_db('../data/article02clean.xml', nlp)
        a3 = add_article_to_db('../data/article03clean.xml', nlp)

    def test_request_article(self):
        """
        Tests that requesting an article returns the right format
        """
        c = Client()
        response = c.get('api/loadContent/')
        print(response)
