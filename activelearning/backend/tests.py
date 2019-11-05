from django.test import TestCase
from backend.models import Article, UserLabel
from backend.helpers import add_article_to_db, add_user_labels_to_db
import spacy


class ArticleTestCase(TestCase):

    def setUp(self):
        # Load the language model
        nlp = spacy.load('fr_core_news_md')

        # Add the articles to the database
        a1 = add_article_to_db('../data/article01clean.xml', nlp)
        a2 = add_article_to_db('../data/article02clean.xml', nlp)

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
            print('Labels: ', labels)
            print(label_counts[99 - 1:129 + 1])

