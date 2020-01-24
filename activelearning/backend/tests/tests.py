from django.test import TestCase

from backend.db_management import add_user_label_to_db, add_article_to_db
from backend.frontend_parsing.postgre_to_frontend import *
from backend.frontend_parsing.frontend_to_postgre import *
from backend.helpers import *
import spacy
import random

# Load the language model
nlp = spacy.load('fr_core_news_md')


class HelperTestCase(TestCase):

    def setUp(self):
        # Add the articles to the database
        self.a1 = add_article_to_db('../data/article01.xml', nlp)

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
        add_user_label_to_db(1111, self.a1.id, 0, label1, a1, True)
        self.assertTrue(is_sentence_labelled(self.a1, 0, 3, 0.75))

        add_user_label_to_db(1111, self.a1.id, 4, label2, a1, True)
        add_user_label_to_db(2222, self.a1.id, 4, label3, a2, False)
        self.assertTrue(is_sentence_labelled(self.a1, 4, 3, 0.75))

        # When no admin label is present
        add_user_label_to_db(3333, self.a1.id, 6, label4, a1, False)
        add_user_label_to_db(4444, self.a1.id, 6, label1, a1, False)
        add_user_label_to_db(5555, self.a1.id, 6, label2, a2, False)
        add_user_label_to_db(6666, self.a1.id, 6, label2, a3, False)
        self.assertFalse(is_sentence_labelled(self.a1, 6, 3, 0.75))

        add_user_label_to_db(3333, self.a1.id, 7, label1, a1, False)
        add_user_label_to_db(4444, self.a1.id, 7, label2, a1, False)
        add_user_label_to_db(5555, self.a1.id, 7, label3, a1, False)
        add_user_label_to_db(6666, self.a1.id, 7, label4, a1, False)
        self.assertFalse(is_sentence_labelled(self.a1, 7, 4, 0.75))

        add_user_label_to_db(3333, self.a1.id, 11, label1, a1, False)
        add_user_label_to_db(4444, self.a1.id, 11, label1, a1, False)
        add_user_label_to_db(5555, self.a1.id, 11, label2, a2, False)
        self.assertFalse(is_sentence_labelled(self.a1, 11, 3, 0.75))

        add_user_label_to_db(3333, self.a1.id, 8, label1, a1, False)
        add_user_label_to_db(4444, self.a1.id, 8, label1, a1, False)
        add_user_label_to_db(5555, self.a1.id, 8, label3, a1, False)
        add_user_label_to_db(6666, self.a1.id, 8, label4, a1, False)
        self.assertTrue(is_sentence_labelled(self.a1, 8, 3, 0.75))

        add_user_label_to_db(3333, self.a1.id, 9, label1, a1, False)
        add_user_label_to_db(4444, self.a1.id, 9, label1, a1, False)
        add_user_label_to_db(5555, self.a1.id, 9, label1, a1, False)
        self.assertTrue(is_sentence_labelled(self.a1, 9, 3, 0.75))

        add_user_label_to_db(3333, self.a1.id, 10, label1, a1, False)
        add_user_label_to_db(4444, self.a1.id, 10, label1, a1, False)
        add_user_label_to_db(5555, self.a1.id, 10, label2, a1, False)
        self.assertTrue(is_sentence_labelled(self.a1, 10, 3, 0.75))

    def test_is_article_labelled(self):
        # Missing labels
        sentence_ids = range(len(self.a1.sentences['sentences']))
        user_id = 1111
        labels = [1, 1, 0, 0, 0]
        author = [37]
        for s in sentence_ids[1:]:
            add_user_label_to_db(user_id, self.a1.id, s, labels, author, True)
        self.assertFalse(is_article_labelled(self.a1, 10, 0.999))
        # All admin labels
        add_user_label_to_db(user_id, self.a1.id, 0, labels, author, True)
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

    def test_clean_user_labels_no_quote1(self):
        """ Test for when no text is annotated as a quote for a single sentence as a task, and no extra text. """
        sentence_ends = [12, 34, 45, 92, 110, 123, 146]
        task_indices = [1]
        first_sentence = 1
        last_sentence = 1
        labels = (34 - 13 + 1) * [0]
        authors = []
        clean_labels = clean_user_labels(sentence_ends, task_indices, first_sentence, last_sentence, labels, authors)
        self.assertEquals(clean_labels, [{'index': 1, 'labels': labels, 'authors': []}])

    def test_clean_user_labels_no_quote2(self):
        """ Test for when no text is annotated as a quote for a single sentence as a task, with extra text. """
        sentence_ends = [12, 34, 45, 92, 110, 123, 146]
        task_indices = [3]
        first_sentence = 3
        last_sentence = 5
        labels = (123 - 46 + 1) * [0]
        authors = []
        clean_labels = clean_user_labels(sentence_ends, task_indices, first_sentence, last_sentence, labels, authors)
        self.assertEquals(clean_labels, [{'index': 3, 'labels': (92 - 46 + 1)*[0], 'authors': []}])

    def test_clean_user_labels_no_quote3(self):
        """ Test for when no text is annotated as a quote for a single sentence as a task, with extra text. """
        sentence_ends = [12, 34, 45, 92, 110, 123, 146]
        task_indices = [2]
        first_sentence = 0
        last_sentence = 4
        labels = (110 - 0 + 1) * [0]
        authors = []
        clean_labels = clean_user_labels(sentence_ends, task_indices, first_sentence, last_sentence, labels, authors)
        self.assertEquals(clean_labels, [{'index': 2, 'labels': labels[35:46], 'authors': []}])

    def test_clean_user_labels_quote1(self):
        """ Test for when text is annotated as a quote for a single sentence as a task, and no extra text. """
        sentence_ends = [12, 34, 45, 92, 110, 123, 146]
        task_indices = [1]
        first_sentence = 1
        last_sentence = 1
        labels = (34 - 13 + 1) * [0]
        labels[5:9] = (9 - 5) * [1]
        authors = [12, 13]
        clean_labels = clean_user_labels(sentence_ends, task_indices, first_sentence, last_sentence, labels, authors)
        self.assertEquals(clean_labels, [{'index': 1, 'labels': labels, 'authors': [25, 26]}])

    def test_clean_user_labels_quote2(self):
        """ Test for when text is annotated as a quote for a single sentence as a task, with extra text. No extra text
        is annotated as part of the quote"""
        sentence_ends = [12, 34, 45, 92, 110, 123, 146]
        task_indices = [1]
        first_sentence = 0
        last_sentence = 3
        labels = (92 - 0 + 1) * [0]
        labels[16:25] = (25 - 16) * [1]
        authors = [2, 3]
        clean_labels = clean_user_labels(sentence_ends, task_indices, first_sentence, last_sentence, labels, authors)
        self.assertEquals(clean_labels, [{'index': 1, 'labels': labels[13:35], 'authors': [2, 3]}])

    def test_clean_user_labels_quote3(self):
        """ Test for when extra text is annotated as a quote, with none of the task text labeled in the quote. """
        sentence_ends = [12, 34, 45, 92, 110, 123, 146]
        task_indices = [1]
        first_sentence = 0
        last_sentence = 3
        labels = (92 - 0 + 1) * [0]
        labels[0:9] = (9 - 0) * [1]
        authors = [2, 3]
        clean_labels = clean_user_labels(sentence_ends, task_indices, first_sentence, last_sentence, labels, authors)
        self.assertEquals(clean_labels, [{'index': 1, 'labels': labels[13:35], 'authors': []}])

    def test_clean_user_labels_quote4(self):
        """ Test for when extra text is annotated as a quote, with none of the task text labeled in the quote. """
        sentence_ends = [12, 34, 45, 92, 110, 123, 146]
        task_indices = [1]
        first_sentence = 0
        last_sentence = 3
        labels = (92 - 0 + 1) * [0]
        labels[35:45] = (45 - 35) * [1]
        authors = [2, 3]
        clean_labels = clean_user_labels(sentence_ends, task_indices, first_sentence, last_sentence, labels, authors)
        self.assertEquals(clean_labels, [{'index': 1, 'labels': labels[13:35], 'authors': []}])

    def test_clean_user_labels_quote5(self):
        """ Test for when extra text is annotated as a quote, with some of the task text also labeled in the quote. """
        sentence_ends = [12, 34, 45, 92, 110, 123, 146]
        task_indices = [1]
        first_sentence = 0
        last_sentence = 3
        labels = (92 - 0 + 1) * [0]
        labels[34:50] = (50 - 34) * [1]
        authors = [2, 3]
        clean_labels = clean_user_labels(sentence_ends, task_indices, first_sentence, last_sentence, labels, authors)
        self.assertEquals(clean_labels, [{'index': 1, 'labels': labels[13:35], 'authors': [2, 3]},
                                         {'index': 2, 'labels': labels[35:46], 'authors': [2, 3]},
                                         {'index': 3, 'labels': labels[46:93], 'authors': [2, 3]}])

    def test_clean_user_labels_quote6(self):
        """ Test for when extra text is annotated as a quote, with some of the task text also labeled in the quote. """
        sentence_ends = [12, 34, 45, 92, 110, 123, 146]
        task_indices = [1]
        first_sentence = 0
        last_sentence = 3
        labels = (92 - 0 + 1) * [0]
        labels[0:30] = (30 - 0) * [1]
        authors = [2, 3]
        clean_labels = clean_user_labels(sentence_ends, task_indices, first_sentence, last_sentence, labels, authors)
        self.assertEquals(clean_labels, [{'index': 1, 'labels': labels[13:35], 'authors': [2, 3]},
                                         {'index': 0, 'labels': labels[0:13], 'authors': [2, 3]}])

    def test_add_user_label_to_db(self):
        article_id = self.a1.id
        session_id = '0000'
        labels = [0, 0, 0, 1]
        sentence_index = 0
        author_index = [0]
        add_user_label_to_db(session_id, article_id, sentence_index, labels, author_index, admin=False)
        all_labels = [label for label in UserLabel.objects.all()]
        self.assertEquals(len(all_labels), 1)
        label = all_labels[0]
        self.assertEquals(label.article, self.a1)
        self.assertEquals(label.session_id, session_id)
        self.assertEquals(label.labels['labels'], labels)
        self.assertEquals(label.sentence_index, sentence_index)
        self.assertEquals(label.author_index['author_index'], author_index)

        session_id_1 = '1234'
        labels_1 = [1, 1, 0, 1]
        sentence_index_1 = 12
        author_index_1 = [88, 89, 90, 91]
        add_user_label_to_db(session_id_1, article_id, sentence_index_1, labels_1, author_index_1, admin=True)
        all_labels = [label for label in UserLabel.objects.all()]
        self.assertEquals(len(all_labels), 2)
        if all_labels[0].session_id == '0000':
            label = all_labels[0]
            label_1 = all_labels[1]
        else:
            label = all_labels[1]
            label_1 = all_labels[0]
        self.assertEquals(label.article, self.a1)
        self.assertEquals(label.session_id, session_id)
        self.assertEquals(label.labels['labels'], labels)
        self.assertEquals(label.sentence_index, sentence_index)
        self.assertEquals(label.author_index['author_index'], author_index)
        self.assertEquals(label_1.article, self.a1)
        self.assertEquals(label_1.session_id, session_id_1)
        self.assertEquals(label_1.labels['labels'], labels_1)
        self.assertEquals(label_1.sentence_index, sentence_index_1)
        self.assertEquals(label_1.author_index['author_index'], author_index_1)


class TaskLoadingTestCase(TestCase):

    def setUp(self):
        # Add the articles to the database
        self.a1 = add_article_to_db('../data/article01.xml', nlp)
        self.a2 = add_article_to_db('../data/article02clean.xml', nlp)
        self.a3 = add_article_to_db('../data/article03clean.xml', nlp)

    def test_load_paragraph_above(self):
        data = load_paragraph_above(self.a1.id, 0)
        self.assertEquals(data['data'], [])
        data = load_paragraph_above(self.a1.id, 1)
        self.assertEquals(data['data'], ["Comment ", "les ", "chouettes ", "effraies ", "au ", "plumage ", "blanc",
                                         ", ", "particulièrement ", "visibles ", "la ", "nuit", ", ", "parviennent",
                                         "-", "elles ", "à ", "attraper ", "des ", "proies", "? "])
        data = load_paragraph_above(self.a1.id, 2)
        self.assertEquals(data['data'], ["Comment ", "les ", "chouettes ", "effraies ", "au ", "plumage ", "blanc",
                                         ", ", "particulièrement ", "visibles ", "la ", "nuit", ", ", "parviennent",
                                         "-", "elles ", "à ", "attraper ", "des ", "proies", "? ", "L’", "énigme ",
                                         "était ", "cachée ", "dans ", "les ", "cycles ", "de ", "la ", "lune ",
                                         "et ", "dans ", "un ", "curieux ", "comportement ", "de ", "ses ", "proies",
                                         ", ", "révèle ", "une ", "étude ", "lausannoise", "."])
        return

    def test_load_paragraph_below(self):
        data = load_paragraph_below(self.a1.id, 0)
        self.assertEquals(data['data'], ["L’", "énigme ", "était ", "cachée ", "dans ", "les ", "cycles ", "de ", "la ",
                                         "lune ", "et ", "dans ", "un ", "curieux ", "comportement ", "de ", "ses ",
                                         "proies", ", ", "révèle ", "une ", "étude ", "lausannoise", "."])
        data = load_paragraph_below(self.a1.id, 1)
        self.assertEquals(data['data'], ["Les ", "nuits ", "de ", "pleine ", "lune", ", ", "tous ", "les ",
                                         "sortilèges ", "sont ", "de ", "mise", ". ", "Les ", "loups-garous ", "se ",
                                         "déchaînent", "; ", "les ", "vampires ", "se ", "régénèrent", "; ", "et ",
                                         "les ", "jeunes ", "filles ", "se ", "muent ", "en ", "sirènes", ". ", "Même ",
                                         "les ", "chouettes ", "effraies ", "(", "Tyto ", "alba", ") ", "sont ", "de ",
                                         "la ", "partie", ". ", "Comme ", "chaque ", "nuit", ", ", "elles ", "partent ",
                                         "en ", "chasse", ". ", "Mais ", "\"", "les ", "nuits ", "de ", "pleine ",
                                         "lune", ", ", "les ", "plus ", "claires ", "d’", "entre ", "elles ",
                                         "resplendissent ", "comme ", "des ", "soleils", "\"", ", ", "observe ",
                                         "Alexandre ", "Roulin", ", ", "de ", "l’", "Université ", "de ", "Lausanne",
                                         ". ", "Comme ", "camouflage ", "vis-à-vis ", "des ", "proies", ", ", "il ",
                                         "y ", "a ", "mieux", "!"])
        data = load_paragraph_below(self.a1.id, 2)
        self.assertEquals(data['data'], ["Les ", "loups-garous ", "se ",
                                         "déchaînent", "; ", "les ", "vampires ", "se ", "régénèrent", "; ", "et ",
                                         "les ", "jeunes ", "filles ", "se ", "muent ", "en ", "sirènes", ". ", "Même ",
                                         "les ", "chouettes ", "effraies ", "(", "Tyto ", "alba", ") ", "sont ", "de ",
                                         "la ", "partie", ". ", "Comme ", "chaque ", "nuit", ", ", "elles ", "partent ",
                                         "en ", "chasse", ". ", "Mais ", "\"", "les ", "nuits ", "de ", "pleine ",
                                         "lune", ", ", "les ", "plus ", "claires ", "d’", "entre ", "elles ",
                                         "resplendissent ", "comme ", "des ", "soleils", "\"", ", ", "observe ",
                                         "Alexandre ", "Roulin", ", ", "de ", "l’", "Université ", "de ", "Lausanne",
                                         ". ", "Comme ", "camouflage ", "vis-à-vis ", "des ", "proies", ", ", "il ",
                                         "y ", "a ", "mieux", "!"])

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
