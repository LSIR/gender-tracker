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


def relative_author_positions(authors, sentence_start):
    relative_authors = []
    for a in authors:
        relative_authors.append(a - sentence_start)
    return relative_authors


class ApiTestCase(TestCase):
    # Load the language model
    nlp = spacy.load('fr_core_news_md')

    def add_sentence_labels(self, client, p_index, s_index, s):
        response = client.get('/api/loadContent/')
        article_id, paragraph_id, sentence_ids, text, task = parse_load_data(response)
        sentence_ends = Article.objects.get(id=article_id).sentences['sentences']
        if s_index == 0:
            sentence_start = 0
        else:
            sentence_start = sentence_ends[s_index - 1] + 1
        tags = s['labels']
        authors = s['authors']
        relative_authors = []
        for a in authors:
            relative_authors.append(a - sentence_start)
        # Check that the correct paragraph is being annotated
        self.assertEqual(paragraph_id, p_index)
        # Check that the correct sentence is being annotated
        self.assertEqual(len(sentence_ids), 1)
        self.assertEqual(s_index, sentence_ids[0])
        # Check that the labels are the same length as the sentence
        self.assertEqual(len(text), len(tags))
        # Check that the text is the same
        self.assertEqual(s['tokens'], text)
        # Return response
        data = {
            'article_id': article_id,
            'paragraph_id': paragraph_id,
            'sentence_id': sentence_ids,
            'tags': tags,
            'authors': relative_authors,
        }
        client.post('/api/submitTags/', data, content_type='application/json')

    def setUp(self):
        # Add the articles to the database
        a1 = add_article_to_db('../data/article01.xml', self.nlp)

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
            'authors': [0],
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
        tags_1 = [0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        tags_2 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]
        tags = tags_1 + tags_2
        # Return response
        data = {
            'article_id': article_id,
            'paragraph_id': paragraph_id,
            'sentence_id': sentence_ids,
            'tags': tags,
            'authors': [15, 41, 42, 43],
        }
        c.post('/api/submitTags/', data, content_type='application/json')
        article = Article.objects.get(id=article_id)
        labels = [label for label in UserLabel.objects.all()]
        self.assertEqual(len(labels), 2)
        self.assertEqual(labels[0].labels['labels'], tags_1)
        self.assertEqual(labels[1].labels['labels'], tags_2)
        self.assertEqual(labels[0].sentence_index, 0)
        self.assertEqual(labels[1].sentence_index, 1)
        self.assertEqual(labels[0].author_index['author_index'], [15, 41, 42, 43])
        self.assertEqual(labels[1].author_index['author_index'], [15, 41, 42, 43])

    def test_label_two_sents(self):
        with open('../data/article01JSON.txt', 'r') as file:
            tagged_data = json.load(file)
        paragraphs = tagged_data['paragraphs']

        c1 = Client()
        # As the 3rd sentence of the 6th paragraph is a 2-line quote, it should be returned as 1 sentence to tag. We
        # start by having a client tag the sentences up to there
        sentence_index = 0
        for p_index, p in enumerate(paragraphs[:6]):
            sentences = p['sentences']
            for s in sentences:
                self.add_sentence_labels(c1, p_index, sentence_index, s)
                sentence_index += 1

        p6 = paragraphs[6]
        s6 = p6['sentences']
        for s in s6[:2]:
            self.add_sentence_labels(c1, 6, sentence_index, s)
            sentence_index += 1

        # Two sentences should be returned
        response = c1.get('/api/loadContent/')
        article_id, paragraph_id, sentence_ids, text, task = parse_load_data(response)
        # Information that should be equal to the information received
        s_index = [sentence_index, sentence_index + 1]
        tags = s6[2]['labels'] + s6[3]['labels']
        tokens = s6[2]['tokens'] + s6[3]['tokens']
        authors = s6[2]['authors']
        # Check that both sentences have the same authors
        self.assertEqual(s6[2]['authors'], s6[3]['authors'])
        sentence_start = Article.objects.get(id=article_id).sentences['sentences'][sentence_index - 1] + 1
        relative_authors = []
        for a in authors:
            relative_authors.append(a - sentence_start)

        # Check that the correct paragraph is being annotated
        self.assertEqual(paragraph_id, 6)
        # Check that the correct sentence is being annotated
        self.assertEqual(len(sentence_ids), 2)
        self.assertEqual(s_index, sentence_ids)
        # Check that the labels are the same length as the sentence
        self.assertEqual(len(text), len(tags))
        # Check that the text is the same
        self.assertEqual(tokens, text)
        # Return response
        data = {
            'article_id': article_id,
            'paragraph_id': paragraph_id,
            'sentence_id': sentence_ids,
            'tags': tags,
            'authors': relative_authors,
        }
        c1.post('/api/submitTags/', data, content_type='application/json')

        article = Article.objects.get(id=article_id)
        user_id = c1.session.get('user')
        # Check that the labels have been added for both sentences
        label1 = UserLabel.objects.filter(article=article, session_id=user_id, sentence_index=sentence_index)[0]
        label2 = UserLabel.objects.filter(article=article, session_id=user_id, sentence_index=sentence_index + 1)[0]
        self.assertEqual(label1.labels['labels'], s6[2]['labels'])
        self.assertEqual(label2.labels['labels'], s6[3]['labels'])
        self.assertEqual(label1.author_index['author_index'], s6[2]['authors'])
        self.assertEqual(label2.author_index['author_index'], s6[3]['authors'])




































