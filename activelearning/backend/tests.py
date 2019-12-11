from django.test import TestCase
from backend.models import Article, UserLabel
from backend.task_loading import *
from backend.task_parsing import *
from backend.helpers import *
import spacy
import random


# Load the language model
nlp = spacy.load('fr_core_news_md')


class HelperTestCase(TestCase):

    def setUp(self):
        # Add the articles to the database
        self.a1 = add_article_to_db('../data/article01.xml', nlp)

    def test_paragraph_sentences(self):
        self.assertEquals(paragraph_sentences(self.a1, -1), (-1, -1))
        self.assertEquals(paragraph_sentences(self.a1, 0), (0, 1))
        self.assertEquals(paragraph_sentences(self.a1, 1), (2, 8))
        self.assertEquals(paragraph_sentences(self.a1, 7), (37, 46))
        self.assertEquals(paragraph_sentences(self.a1, 8), (-1, -1))

    def test_label_consensus(self):
        label1 = [0, 1, 1, 1, 1, 0, 0]
        label2 = [0, 1, 1, 1, 1, 0, 0]
        label3 = [0, 1, 1, 1, 1, 1, 0]
        label4 = [0, 0, 1, 1, 1, 0, 0]
        label5 = [0, 1, 1, 1, 1, 0, 0]
        labels = [label1, label2, label3, label4, label5]
        authors = [[37, 38], [62, 63, 64], [37, 38, 39], [37, 38], [37, 38]]
        label, author, cons = label_consensus(labels, authors)
        self.assertEquals(label, [0, 1, 1, 1, 1, 0, 0])
        self.assertEquals(author, [37, 38])
        self.assertEquals(cons, (3 + 3) / (2 * len(labels)))
        label1 = [0, 1, 1, 1, 1, 0, 0]
        label2 = [0, 1, 1, 1, 1, 1, 0]
        label3 = [0, 1, 1, 1, 1, 1, 0]
        label4 = [0, 1, 1, 1, 1, 1, 0]
        label5 = [0, 1, 1, 1, 1, 1, 0]
        labels = [label1, label2, label3, label4, label5]
        authors = [[37, 38], [62, 63, 64], [62, 63, 64], [37, 38], [62, 63, 64]]
        label, author, cons = label_consensus(labels, authors)
        self.assertEquals(label, [0, 1, 1, 1, 1, 1, 0])
        self.assertEquals(author, [62, 63, 64])
        self.assertEquals(cons, (4 + 3) / (2 * len(labels)))

    def test_is_sentence_labelled(self):
        # When an admin label is present
        label1 = [0, 1, 1, 1, 1, 0, 0]
        label2 = [0, 1, 1, 1, 1, 1, 0]
        label3 = [0, 1, 1, 1, 1, 0, 1]
        label4 = [0, 0, 1, 1, 1, 0, 1]
        a1 = [66]
        a2 = [66, 67]
        a3 = [65, 66]
        add_user_labels_to_db(self.a1.id, 1111, label1, 0, a1, True)
        self.assertTrue(is_sentence_labelled(self.a1, 0, 3, 0.75))

        add_user_labels_to_db(self.a1.id, 1111, label2, 4, a1, True)
        add_user_labels_to_db(self.a1.id, 2222, label3, 4, a2, False)
        self.assertTrue(is_sentence_labelled(self.a1, 4, 3, 0.75))

        # When no admin label is present
        add_user_labels_to_db(self.a1.id, 3333, label4, 6, a1, False)
        add_user_labels_to_db(self.a1.id, 4444, label1, 6, a1, False)
        add_user_labels_to_db(self.a1.id, 5555, label2, 6, a2, False)
        add_user_labels_to_db(self.a1.id, 6666, label2, 6, a3, False)
        self.assertFalse(is_sentence_labelled(self.a1, 6, 3, 0.75))

        add_user_labels_to_db(self.a1.id, 3333, label1, 7, a1, False)
        add_user_labels_to_db(self.a1.id, 4444, label2, 7, a1, False)
        add_user_labels_to_db(self.a1.id, 5555, label3, 7, a1, False)
        add_user_labels_to_db(self.a1.id, 6666, label4, 7, a1, False)
        self.assertFalse(is_sentence_labelled(self.a1, 7, 4, 0.75))

        add_user_labels_to_db(self.a1.id, 3333, label1, 11, a1, False)
        add_user_labels_to_db(self.a1.id, 4444, label1, 11, a1, False)
        add_user_labels_to_db(self.a1.id, 5555, label2, 11, a2, False)
        self.assertFalse(is_sentence_labelled(self.a1, 11, 3, 0.75))

        add_user_labels_to_db(self.a1.id, 3333, label1, 8, a1, False)
        add_user_labels_to_db(self.a1.id, 4444, label1, 8, a1, False)
        add_user_labels_to_db(self.a1.id, 5555, label3, 8, a1, False)
        add_user_labels_to_db(self.a1.id, 6666, label4, 8, a1, False)
        self.assertTrue(is_sentence_labelled(self.a1, 8, 3, 0.75))

        add_user_labels_to_db(self.a1.id, 3333, label1, 9, a1, False)
        add_user_labels_to_db(self.a1.id, 4444, label1, 9, a1, False)
        add_user_labels_to_db(self.a1.id, 5555, label1, 9, a1, False)
        self.assertTrue(is_sentence_labelled(self.a1, 9, 3, 0.75))

        add_user_labels_to_db(self.a1.id, 3333, label1, 10, a1, False)
        add_user_labels_to_db(self.a1.id, 4444, label1, 10, a1, False)
        add_user_labels_to_db(self.a1.id, 5555, label2, 10, a1, False)
        self.assertTrue(is_sentence_labelled(self.a1, 10, 3, 0.75))

    def test_is_article_labelled(self):
        # Missing labels
        sentence_ids = range(len(self.a1.sentences['sentences']))
        user_id = 1111
        labels = [1, 1, 0, 0, 0]
        author = [37]
        for s in sentence_ids[1:]:
            add_user_labels_to_db(self.a1.id, user_id, labels, s, author, True)
        self.assertFalse(is_article_labelled(self.a1, 10, 0.999))
        # All admin labels
        add_user_labels_to_db(self.a1.id, user_id, labels, 0, author, True)
        self.assertTrue(is_article_labelled(self.a1, 10, 0.999))

    def test_change_confidence(self):
        article = Article.objects.get(id=self.a1.id)
        # Changing confidences
        original_confidence = article.confidence['confidence']
        original_min_confidence = article.confidence['min_confidence']

        self.assertEquals(original_min_confidence, 0)
        new_conf = len(original_confidence) * [80]
        new_min_conf = change_confidence(article.id, new_conf)
        self.assertEquals(new_min_conf, 80)

        # Load the new confidence
        article = Article.objects.get(id=self.a1.id)
        conf = article.confidence['confidence']
        min_conf = article.confidence['min_confidence']
        self.assertEquals(conf, new_conf)
        self.assertEquals(min_conf, 80)

        # Changing confidence with invalid confidence
        conf = [0]
        self.assertIsNone(change_confidence(article.id, conf))
        conf = len(original_confidence) * [-1]
        self.assertIsNone(change_confidence(article.id, conf))


class TaskParsingTestCase(TestCase):

    def setUp(self):
        self.a1 = add_article_to_db('../data/article01.xml', nlp)

    def test_label_edges(self):
        data = label_edges(self.a1, 0, [])
        self.assertEquals(data['token'], (0, 44))
        self.assertEquals(data['sentence'], (0, 1))

        data = label_edges(self.a1, 0, [0, 1])
        self.assertEquals(data['token'], (0, 44))
        self.assertEquals(data['sentence'], (0, 1))

        data = label_edges(self.a1, 0, [0])
        self.assertEquals(data['token'], (0, 20))
        self.assertEquals(data['sentence'], (0, 0))

        data = label_edges(self.a1, 0, [1])
        self.assertEquals(data['token'], (21, 44))
        self.assertEquals(data['sentence'], (1, 1))

        self.assertIsNone(label_edges(self.a1, -1, [1]))
        self.assertIsNone(label_edges(self.a1, 8, []))
        self.assertIsNone(label_edges(self.a1, 100, [1]))
        self.assertIsNone(label_edges(self.a1, 0, [-1]))
        self.assertIsNone(label_edges(self.a1, 0, [1000]))

    def test_add_labels_to_database(self):
        article_id = self.a1.id
        session_id = '0000'
        labels = [0, 0, 0, 1]
        sentence_index = 0
        author_index = [0]
        add_user_labels_to_db(article_id, session_id, labels, sentence_index, author_index, admin=False)

    def test_add_user_labels_to_db(self):
        """  """
        return

    def test_add_article_to_db(self):
        """  """
        return


class TaskLoadingTestCase(TestCase):

    def setUp(self):
        # Add the articles to the database
        a1 = add_article_to_db('../data/article01.xml', nlp)
        a2 = add_article_to_db('../data/article02clean.xml', nlp)
        a3 = add_article_to_db('../data/article03clean.xml', nlp)

        # Default values
        session_id = 1111
        labels = [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        # Add a user label for article 1
        add_user_labels_to_db(a1.id, session_id, labels, 7, [66])

    def test_form_sentence_json(self):
        """  """
        return

    def test_form_paragraph_json(self):
        """  """
        return

    def test_load_paragraph_above(self):
        """  """
        return

    def test_load_paragraph_below(self):
        """  """
        return

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
        return

    def test_quote_start_sentence(self):
        """  """
        return

    def test_quote_end_sentence(self):
        """  """
        return

    def test_request_labelling_task(self):
        """  """
        return
