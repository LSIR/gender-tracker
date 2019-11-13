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
        a2 = add_article_to_db('../data/article02clean.xml', nlp)
        a3 = add_article_to_db('../data/article03clean.xml', nlp)

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
        tokens = article.tokens['tokens'][0:article.sentences['sentences'][1]]
        tags_1 = [0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0]
        tags_2 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 2, 2, 2, 0]
        tags = tags_1 + tags_2
        print(f'\narticle id  : {article_id}')
        print(f'label counts: {article.label_counts["label_counts"]}')
        print(f'tokens      : {tokens}')
        print(f'tags        : {tags}\n')
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
        print(f'\narticle id  : {article_id}')
        print(f'label counts: {article.label_counts["label_counts"]}')
        print(f'tokens      : {tokens}')
        print(f'tags        : {tags}\n')
        for label in labels:
            print(f'\nLabel id  : {label.id}')
            print(f'Article id: {label.article.id}')
            print(f'Sentence  : {label.sentence_index}')
            print(f'Labels  : {label.labels["labels"]}')
            print(f'Author    : {label.author_index["author_index"]}\n')
