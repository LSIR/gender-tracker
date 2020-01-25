from django.test import TestCase
from django.test import Client
from backend.models import Article, UserLabel
from backend.helpers import change_confidence
from backend.db_management import add_article_to_db
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

    def add_sentence_labels(self, client, true_p_id, true_s_ids, sentences):
        # Load the article through the api
        response = client.get('/api/loadContent/')
        article_id, paragraph_id, sentence_ids, text, task = parse_load_data(response)

        # Load the tags and authors
        tags = []
        authors = []
        for sentence in sentences:
            tags += sentence['labels']
            authors += sentence['authors']

        # Find the relative token indices
        sentence_ends = Article.objects.get(id=article_id).sentences['sentences']
        first_sentence = true_s_ids[0]
        if first_sentence == 0:
            first_token_id = 0
        else:
            first_token_id = sentence_ends[first_sentence - 1] + 1
        relative_authors = []
        for a in authors:
            relative_authors.append(a - first_token_id)

        # Check that the task is sentence labelling
        self.assertEqual(task, 'sentence')
        # Check that the correct paragraph is being annotated
        self.assertEqual(paragraph_id, true_p_id)
        # Check that the correct sentences are being annotated
        self.assertEqual(sentence_ids, true_s_ids)
        # Check that the labels are the same length as the sentence
        self.assertEqual(len(text), len(tags))
        # Check that the text is the same
        sentence_text = []
        for s in sentences:
            sentence_text += s['tokens']
        self.assertEqual(text, sentence_text)
        # Return response
        data = {
            'article_id': article_id,
            'paragraph_id': true_p_id,
            'sentence_id': true_s_ids,
            'first_sentence': sentence_ids[0],
            'last_sentence': sentence_ids[-1],
            'tags': tags,
            'authors': relative_authors,
        }
        response = client.post('/api/submitTags/', data, content_type='application/json')
        self.assertTrue(json.loads(response.content)['success'])

    def setUp(self):
        # Add the articles to the database
        a1 = add_article_to_db('../data/article01.xml', self.nlp)

    def test_basic_tag_submit(self):
        """
        Tests that requesting an article returns the right format
        """
        c = Client()
        response = c.get('/api/loadContent/')
        user_id = c.session['id']
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
            'first_sentence': sentence_ids[0],
            'last_sentence': sentence_ids[-1],
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
        # To set a session key
        response = c.get('/api/loadContent/')
        article = Article.objects.all()[0]
        article_id = article.id
        paragraph_id = 0
        sentence_ids = [0, 1]
        tags_1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]
        tags_2 = [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        tags = tags_1 + tags_2
        # Return response
        data = {
            'article_id': article_id,
            'paragraph_id': paragraph_id,
            'sentence_id': sentence_ids,
            'first_sentence': sentence_ids[0],
            'last_sentence': sentence_ids[-1],
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
                self.add_sentence_labels(c1, p_index, [sentence_index], [s])
                sentence_index += 1

        p6 = paragraphs[6]
        s6 = p6['sentences']
        for s in s6[:2]:
            self.add_sentence_labels(c1, 6, [sentence_index], [s])
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
            'first_sentence': sentence_ids[0],
            'last_sentence': sentence_ids[-1],
            'tags': tags,
            'authors': relative_authors,
        }
        c1.post('/api/submitTags/', data, content_type='application/json')

        article = Article.objects.get(id=article_id)
        user_id = c1.session['id']
        # Check that the labels have been added for both sentences
        label1 = UserLabel.objects.filter(article=article, session_id=user_id, sentence_index=sentence_index)[0]
        label2 = UserLabel.objects.filter(article=article, session_id=user_id, sentence_index=sentence_index + 1)[0]
        self.assertEqual(label1.labels['labels'], s6[2]['labels'])
        self.assertEqual(label2.labels['labels'], s6[3]['labels'])
        self.assertEqual(label1.author_index['author_index'], s6[2]['authors'])
        self.assertEqual(label2.author_index['author_index'], s6[3]['authors'])

    def test_label_full_article(self):
        with open('../data/article01JSON.txt', 'r') as file:
            tagged_data = json.load(file)
        paragraphs = tagged_data['paragraphs']

        c1 = Client()
        c2 = Client()

        # Sentences 2 and 3 from p. 6 need to be counted as a single sentence, as they belong to a single quote.
        # Sentences 0, 1, 2 and 3 from p. 7 need to be counted as a single sentence, as they belong to a single quote.

        # Label all sentences
        sentence_index = 0
        for p_index, p in enumerate(paragraphs):
            sentences = p['sentences']
            for s_index, s in enumerate(sentences):
                # Check that this isn't one of the last sentences of a grouped sentence.
                if not ((p_index == 6 and s_index in [3]) or
                        (p_index == 7 and s_index in [1, 2, 3])):
                    # If it's the last sentence of a grouped sentence, load the grouped tags
                    if p_index == 6 and s_index == 2:
                        true_p_id = 6
                        true_s_ids = [sentence_index, sentence_index + 1]
                        true_sentences = [sentences[s_index], sentences[s_index + 1]]
                    elif p_index == 7 and s_index == 0:
                        true_p_id = 7
                        true_s_ids = [sentence_index, sentence_index + 1, sentence_index + 2, sentence_index + 3]
                        true_sentences = [sentences[s_index], sentences[s_index + 1],
                                          sentences[s_index + 2], sentences[s_index + 3]]
                    else:
                        true_p_id = p_index
                        true_s_ids = [sentence_index]
                        true_sentences = [s]
                    self.add_sentence_labels(c1, true_p_id, true_s_ids, true_sentences)
                sentence_index += 1
        # Check label counts
        article = Article.objects.all()[0]
        label_counts = article.label_counts['label_counts']
        for c in label_counts:
            self.assertEquals(c, 1)
        self.assertEquals(article.label_counts['min_label_counts'], 1)

        # Check that c2 loads the first sentences
        """ ONLY WHEN NON ADMIN """
        """
        sentences = paragraphs[0]['sentences']
        sentence_index = 0
        for s_index, s in enumerate(sentences):
            true_p_id = 0
            true_s_ids = [sentence_index]
            true_sentences = [s]
            self.add_sentence_labels(c2, true_p_id, true_s_ids, true_sentences)
            sentence_index += 1
        # Check label counts
        article = Article.objects.all()[0]
        label_counts = article.label_counts['label_counts']
        for i, c in enumerate(label_counts):
            if i < sentence_index:
                self.assertEquals(c, 2)
            else:
                self.assertEquals(c, 1)
        self.assertEquals(article.label_counts['min_label_counts'], 1)
        """

    def test_high_confidence_paragraph(self):
        with open('../data/article01JSON.txt', 'r') as file:
            tagged_data = json.load(file)
        paragraphs = tagged_data['paragraphs']

        # Change article confidence for paragraph 2
        article = Article.objects.all()[0]
        p_ends = article.paragraphs['paragraphs']
        confidence = article.confidence['confidence']
        for index in range(p_ends[0], p_ends[1] + 1):
            confidence[index] = 90
        change_confidence(article.id, confidence)
        c = Client()

        # All sentences from the first paragraph should still have confidence 0
        sentence_index = 0
        sentences = paragraphs[0]['sentences']
        for s_index, s in enumerate(sentences):
            true_p_id = 0
            true_s_ids = [sentence_index]
            true_sentences = [s]
            self.add_sentence_labels(c, true_p_id, true_s_ids, true_sentences)
            sentence_index += 1

        # The second paragraph should be returned as a block
        response = c.get('/api/loadContent/')
        article_id, paragraph_id, sentence_ids, text, task = parse_load_data(response)
        self.assertEquals(article_id, article.id)
        self.assertEquals(paragraph_id, 1)
        self.assertEquals(sentence_ids, [2, 3, 4, 5, 6, 7, 8])
        self.assertEquals(task, 'paragraph')
        # Check paragraph 2 data
        tokens = []
        for s in paragraphs[1]['sentences']:
            tokens += s['tokens']
        self.assertEquals(text, tokens)
        # Return tags
        # Return response
        data = {
            'article_id': article_id,
            'paragraph_id': 1,
            'sentence_id': sentence_ids,
            'first_sentence': sentence_ids[0],
            'last_sentence': sentence_ids[-1],
            'tags': len(text) * [0],
            'authors': [],
        }
        c.post('/api/submitTags/', data, content_type='application/json')

        # The third paragraph should be sentences again
        sentence_index = len(paragraphs[0]['sentences']) + len(paragraphs[1]['sentences'])
        sentences = paragraphs[2]['sentences']
        for s_index, s in enumerate(sentences):
            true_p_id = 2
            true_s_ids = [sentence_index]
            true_sentences = [s]
            self.add_sentence_labels(c, true_p_id, true_s_ids, true_sentences)
            sentence_index += 1

        # Check label counts
        article = Article.objects.all()[0]
        label_counts = article.label_counts['label_counts']
        for i, count in enumerate(label_counts):
            if i < sentence_index:
                self.assertEquals(count, 1)
            else:
                self.assertEquals(count, 0)
        self.assertEquals(article.label_counts['min_label_counts'], 0)




















