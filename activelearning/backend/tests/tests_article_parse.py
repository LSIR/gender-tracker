from django.test import TestCase
from backend.models import Article
from backend.db_management import add_article_to_db
import spacy
import json


class ArticleParsingTestCase(TestCase):
    # Load the language model
    nlp = spacy.load('fr_core_news_md')

    def setUp(self):
        # Add the articles to the database
        add_article_to_db('../data/article01.xml', self.nlp, 'Heidi.News')

    def test_articles_text(self):
        with open('../data/article01Parsed.txt', 'r') as file:
            parsed_article = json.load(file)
        article = Article.objects.all()[0]
        text = parsed_article['text']
        self.assertEqual(article.text, text)

    def test_articles_tokens(self):
        with open('../data/article01Parsed.txt', 'r') as file:
            parsed_article = json.load(file)
        article = Article.objects.all()[0]
        tokens = parsed_article['tokens']
        self.assertEqual(article.tokens['tokens'], tokens)

    def test_articles_paragraph_ends(self):
        with open('../data/article01Parsed.txt', 'r') as file:
            parsed_article = json.load(file)
        article = Article.objects.all()[0]
        paragraphs = parsed_article['paragraphs']
        self.assertEqual(article.paragraphs['paragraphs'], paragraphs)

    def test_articles_sentence_ends(self):
        with open('../data/article01Parsed.txt', 'r') as file:
            parsed_article = json.load(file)
        article = Article.objects.all()[0]
        sentences = parsed_article['sentences']
        self.assertEqual(article.sentences['sentences'], sentences)

    def test_articles_in_quotes(self):
        with open('../data/article01Parsed.txt', 'r') as file:
            parsed_article = json.load(file)
        article = Article.objects.all()[0]
        in_quotes = parsed_article['in_quotes']
        self.assertEqual(article.in_quotes['in_quotes'], in_quotes)

    def test_articles_confidence(self):
        with open('../data/article01Parsed.txt', 'r') as file:
            parsed_article = json.load(file)
        article = Article.objects.all()[0]
        confidence = parsed_article['confidence']
        self.assertEqual(article.confidence['confidence'], confidence)
        self.assertEqual(article.confidence['min_confidence'], 0)
