from django.test import TestCase
from django.test import Client
from backend.models import Article, UserLabel
from backend.helpers import add_article_to_db, add_user_labels_to_db, load_hardest_articles, request_labelling_task
import spacy
import json


def parse_load_data(response):
    data = json.loads(response.content)
    article_id = data['article_id']
    paragraph_id = data['paragraph_id']
    sentence_id = data['sentence_id']
    text = data['data']
    task = data['task']
    return article_id, paragraph_id, sentence_id, text, task


class ApiTestCase(TestCase):

    def setUp(self):
        # Load the language model
        nlp = spacy.load('fr_core_news_md')
        # Add the articles to the database
        a1 = add_article_to_db('../data/article01clean.xml', nlp)

    def test_basic_tag_submit(self):
        """
        Tests that requesting an article returns the right format
        """
        c = Client()
        response = c.get('/api/loadContent/')
        user_id = c.session.get('user')
        article_id, paragraph_id, sentence_ids, text, task = parse_load_data(response)
        if task == 'sentence':
            tags = len(text) * [0]
            tags[0] = 1
        elif task == 'paragraph':
            tags = [0]
        else:
            tags = []
        # Return response
        data = {
            'article_id': article_id,
            'paragraph_id': paragraph_id,
            'sentence_id': sentence_ids,
            'tags': tags,
        }
        c.post('/api/submitTags/', data, content_type='application/json')
        # Check that the tags have been added to the database and
        # that the label counts have been increased
        article = Article.objects.get(id=article_id)
        # Check that the only sentences with a label are the ones that were just tagged
        label_counts = article.label_counts['label_counts']
        for i in range(len(label_counts)):
            if i in sentence_ids:
                count = 1
            else:
                count = 0
            self.assertEqual(label_counts[i], count)

        labels = [label for label in UserLabel.objects.filter(article=article, session_id=user_id)]
        self.assertEqual(len(labels), 1)
        label = labels[0]
        # Check that the labels are the ones we input
        self.assertEqual(label.labels['labels'], tags)

    def test_tag_multiple_sentences(self):
        c = Client()
        article = Article.objects.all()[0]
        article_id = article.id
        paragraph_id = 0
        sentence_ids = [0, 1]
        tags_1 = [0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0]
        rest_1 = [0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        tags_2 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 2, 2, 2, 0]
        rest_2 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
        tags = tags_1 + tags_2
        # Return response
        data = {
            'article_id': article_id,
            'paragraph_id': paragraph_id,
            'sentence_id': sentence_ids,
            'tags': tags,
        }
        c.post('/api/submitTags/', data, content_type='application/json')
        article = Article.objects.get(id=article_id)
        labels = [label for label in UserLabel.objects.all()]
        self.assertEqual(len(labels), 2)
        self.assertEqual(labels[0].labels['labels'], rest_1)
        self.assertEqual(labels[1].labels['labels'], rest_2)
        self.assertEqual(labels[0].sentence_index, 0)
        self.assertEqual(labels[1].sentence_index, 1)
        self.assertEqual(labels[0].author_index['author_index'], [15, 41, 42, 43])
        self.assertEqual(labels[1].author_index['author_index'], [15, 41, 42, 43])

    def test_tag_full_article(self):
        with open('../data/article01JSON.txt', 'r') as file:
            tagged_data = json.load(file)
        paragraphs = tagged_data['paragraphs']
        sen = []
        for p in paragraphs:
            sentences = p['sentences']
            for s in sentences:
                sen.append(s['sentence'])
        print(sen)
