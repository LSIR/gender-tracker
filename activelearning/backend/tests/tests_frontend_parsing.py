from django.test import TestCase

from backend.frontend_parsing.frontend_to_postgre import *
from backend.frontend_parsing.postgre_to_frontend import *

""" The content and annotation of the first article. """
TEST_ARTICLE = {
    'name': 'Le football',
    'text': '<?xml version="1.0"?>\n'
                '<article>\n'
                '\t<titre>Le football</titre>\n'
                '\t<p>Le fameux joueur de football Diego Maradona est meilleur que Lionel Messi. Du moins, c\'est ce '
                'que pense Serge Aurier. Il l\'affirme dans un interview avec L\'Equipe. Il pense que sa victoire en '
                'coupe du monde est plus importante que les victoires individuelles de lutin du FC Barcelone.</p>\n'
                '\t<p>Il ne pense pas que Messi pourra un jour gagner une coupe du monde. Mais Platini nous informe '
                'qu\'en fait c\'est lui "le meilleur joueur du monde". Et que "ça n\'a rien à voir avec son ego".</p>\n'
                '\t<p>Mais au final, c\'est vraiement Wayne Rooney, le meilleur joueur de tous les temps. C\'est '
                'indiscutable. Même Zlatan le dit: "Personne n\'est meilleur que Wayne".</p>\n'
                '</article>',
    'labeled_xml': '<?xml version="1.0"?>\n'
                  '<article>\n'
                  '\t<titre>Le football</titre>\n'
                  '\t<p><RS a="0">Le fameux joueur de football Diego Maradona est meilleur que Lionel Messi</RS>. Du '
                  'moins, c\'est ce que pense <author a="0">Serge Aurier</author>. Il l\'affirme dans un interview '
                  'avec L\'Equipe. Il pense que <RS a="0">sa victoire en coupe du monde est plus importante que les '
                  'victoires individuelles de lutin du FC Barcelone</RS>.</p>\n'
                  '\t<p>Il ne pense pas que Messi pourra un jour gagner une coupe du monde. Mais <author a="1">Platini '
                  '</author> nous informe qu\'en fait <RS a="1">c\'est lui "le meilleur joueur du monde"</RS>. Et que '
                  '"<RS a="1">ça n\'a rien à voir avec son ego</RS>".</p>\n'
                  '\t<p>Mais au final, c\'est vraiement Wayne Rooney, le meilleur joueur de tous les temps. C\'est '
                  'indiscutable. Même <author a="2">Zlatan </author>le dit: "<RS a="2">Personne n\'est meilleur que '
                  'Wayne</RS>".</p>\n'
                  '</article>',
    'clean': 'Le fameux joueur de football Diego Maradona est meilleur que Lionel Messi. Du moins, c\'est ce que pense '
            'Serge Aurier. Il l\'affirme dans un interview avec L\'Equipe. Il pense que sa victoire en coupe du monde '
            'est plus importante que les victoires individuelles de lutin du FC Barcelone. Il ne pense pas que Messi '
            'pourra un jour gagner une coupe du monde. Mais Platini nous informe qu\'en fait c\'est lui "le meilleur '
            'joueur du monde". Et que "ça n\'a rien à voir avec son ego". Mais au final, c\'est vraiement Wayne Rooney,'
            ' le meilleur joueur de tous les temps. C\'est indiscutable. Même Zlatan le dit: "Personne n\'est meilleur'
            'que Wayne".',
    'tokens': [
        ['Le ', 'fameux ', 'joueur ', 'de ', 'football ', 'Diego ', 'Maradona ', 'est ', 'meilleur ', 'que ', 'Lionel ',
         'Messi', '. '],
        ['Du ', 'moins', ', ', "c'", 'est ', 'ce ', 'que ', 'pense ', 'Serge ', 'Aurier', '. '],
        ['Il ', "l'", 'affirme ', 'dans ', 'un ', 'interview ', 'avec ', "L'", 'Equipe', '. '],
        ['Il ', 'pense ', 'que ', 'sa ', 'victoire ', 'en ', 'coupe ', 'du ', 'monde ', 'est ', 'plus ', 'importante ',
         'que ', 'les ', 'victoires ', 'individuelles ', 'de ', 'lutin ', 'du ', 'FC ', 'Barcelone', '.'],
        ['Il ', 'ne ', 'pense ', 'pas ', 'que ', 'Messi ', 'pourra ', 'un ', 'jour ', 'gagner ', 'une ', 'coupe ',
         'du ', 'monde', '. '],
        ['Mais ', 'Platini ', 'nous ', 'informe ', "qu'", 'en ', 'fait ', "c'", 'est ', 'lui ', '"', 'le ', 'meilleur ',
         'joueur ', 'du ', 'monde', '"', '. '],
        ['Et ', 'que ', '"', 'ça ', "n'", 'a ', 'rien ', 'à ', 'voir ', 'avec ', 'son ', 'ego', '"', '.'],
        ['Mais ', 'au ', 'final', ', ', "c'", 'est ', 'vraiement ', 'Wayne ', 'Rooney', ', ', 'le ', 'meilleur ',
         'joueur ', 'de ', 'tous ', 'les ', 'temps', '. '],
        ["C'", 'est ', 'indiscutable', '. '],
        ['Même ', 'Zlatan ', 'le ', 'dit', ': ', '"', 'Personne ', "n'", 'est ', 'meilleur ', 'que ', 'Wayne', '"', '.']
    ],
    'in_quotes': [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0]
    ],
    'labels': [
        # 0 - 12
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        # 13 - 23
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 24 - 33
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 34 - 55
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        # 56 - 70
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 71 - 88
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        # 89 - 102
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        # 103 - 120
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 121 - 124
        [0, 0, 0, 0],
        # 125 - 138
        [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0]
    ],
    'authors': [
        [21, 22],
        [],
        [],
        [21, 22],
        [],
        [72],
        [72],
        [],
        [],
        [126],
    ],
    'relative_authors': [
        [21, 22],
        [],
        [],
        [8, 9],
        [],
        [1],
        [1],
        [],
        [],
        [1],
    ],
    'sentence_ends': [12, 23, 33, 55, 70, 88, 102, 120, 124, 138],
    'paragraph_ends': [3, 6, 9],
}


class PostgreToFrontendTestCase(TestCase):
    """ Test class for the postgre_to_frontend.py file in the frontend_parsing package """

    def setUp(self):
        """ Adds the test article to the database """
        self.a1 = Article.objects.create(
            name=TEST_ARTICLE['name'],
            text=TEST_ARTICLE['text'],
            people={'people': []},
            tokens={'tokens': [token for sentence_tokens in TEST_ARTICLE['tokens'] for token in sentence_tokens]},
            paragraphs={'paragraphs': TEST_ARTICLE['paragraph_ends']},
            sentences={'sentences': TEST_ARTICLE['sentence_ends']},
            labeled={
                'labeled': len(TEST_ARTICLE['sentence_ends']) * [0],
                'fully_labeled': 0,
            },
            in_quotes={'in_quotes': TEST_ARTICLE['in_quotes']},
            confidence={
                'confidence': len(TEST_ARTICLE['sentence_ends']) * [0],
                'min_confidence': 0,
            },
            admin_article=False,
        )

    def check_keys_form(self, data):
        """ Checks that the keys in the data are correct """
        keys = list(data)
        self.assertEquals(len(keys), 4)
        self.assertTrue('article_id' in keys)
        self.assertTrue('sentence_id' in keys)
        self.assertTrue('data' in keys)
        self.assertTrue('task' in keys)

    def check_keys_load(self, data):
        """ Checks that the keys in the data are correct """
        keys = list(data)
        self.assertEquals(len(keys), 3)
        self.assertTrue('data' in keys)
        self.assertTrue('first_sentence' in keys)
        self.assertTrue('last_sentence' in keys)

    def test_form_sentence_json_0(self):
        """ Tests that the method correctly forms the data for no sentences in the test article correctly. """
        data = form_sentence_json(self.a1, [])
        self.check_keys_form(data)
        self.assertEquals(data['article_id'], self.a1.id)
        self.assertEquals(data['sentence_id'], [])
        self.assertEquals(data['data'], [])
        self.assertEquals(data['task'], 'sentence')

    def test_form_sentence_json_1(self):
        """ Tests that the method correctly forms the data for a single sentence in the test article correctly. """

        def check_single_sentence(sentence_id):
            data = form_sentence_json(self.a1, [sentence_id])
            self.check_keys_form(data)
            self.assertEquals(data['article_id'], self.a1.id)
            self.assertEquals(data['sentence_id'], [sentence_id])
            self.assertEquals(data['data'], TEST_ARTICLE['tokens'][sentence_id])
            self.assertEquals(data['task'], 'sentence')

        for sentence in range(10):
            check_single_sentence(sentence)

    def test_form_sentence_json_2(self):
        """ Tests that the method correctly forms the data for two sentences in the test article correctly. """

        def check_two_sentences(id_1, id_2):
            data = form_sentence_json(self.a1, [id_1, id_2])
            self.check_keys_form(data)
            self.assertEquals(data['article_id'], self.a1.id)
            self.assertEquals(data['sentence_id'], [id_1, id_2])
            self.assertEquals(data['data'], [token for sentence_tokens in TEST_ARTICLE['tokens'][id_1:id_2 + 1]
                                             for token in sentence_tokens]),
            self.assertEquals(data['task'], 'sentence')

        for s1 in range(9):
            check_two_sentences(s1, s1 + 1)

    def test_form_sentence_json_3(self):
        """ Tests that the method correctly forms the data for three sentences in the test article correctly. """

        def check_two_sentences(id_1, id_2, id_3):
            data = form_sentence_json(self.a1, [id_1, id_2, id_3])
            self.check_keys_form(data)
            self.assertEquals(data['article_id'], self.a1.id)
            self.assertEquals(data['sentence_id'], [id_1, id_2, id_3])
            self.assertEquals(data['data'], [token for sentence_tokens in TEST_ARTICLE['tokens'][id_1:id_3 + 1]
                                             for token in sentence_tokens]),
            self.assertEquals(data['task'], 'sentence')

        for s1 in range(8):
            check_two_sentences(s1, s1 + 1, s1 + 2)

    def test_form_paragraph_json_0(self):
        """ Checks that the method works correctly on all 3 paragraphs """

        def check_paragraph(p_id):
            data = form_paragraph_json(self.a1, p_id)
            self.check_keys_form(data)
            first_sentence = 0
            if p_id > 0:
                first_sentence = TEST_ARTICLE['paragraph_ends'][p_id - 1] + 1
            last_sentence = TEST_ARTICLE['paragraph_ends'][p_id]
            tokens = TEST_ARTICLE['tokens'][first_sentence:last_sentence + 1]
            self.assertEquals(data['article_id'], self.a1.id)
            self.assertEquals(data['sentence_id'], list(range(first_sentence, last_sentence + 1)))
            self.assertEquals(data['data'], [token for sentence_tokens in tokens for token in sentence_tokens]),
            self.assertEquals(data['task'], 'paragraph')

        check_paragraph(0)
        check_paragraph(1)
        check_paragraph(2)

    def test_load_paragraph_above_0(self):
        """ Checks that the method works for all sentences in the test article. """
        # Paragraphs: {[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]}

        def check_load_above(sentence, first_sentence, last_sentence):
            data = load_paragraph_above(self.a1.id, sentence)
            self.check_keys_load(data)
            expected_tokens = []
            if first_sentence != -1:
                expected_tokens = TEST_ARTICLE['tokens'][first_sentence:last_sentence + 1]
                expected_tokens = [token for sentence_tokens in expected_tokens for token in sentence_tokens]
            self.assertEquals(data['data'], expected_tokens)
            self.assertEquals(data['first_sentence'], first_sentence)
            self.assertEquals(data['last_sentence'], last_sentence)

        # 0 -> Load nothing
        check_load_above(0, -1, -1)
        # 1 -> Load 0
        check_load_above(1, 0, 0)
        # 2 -> Load 0, 1
        check_load_above(2, 0, 1)
        # 3 -> Load 0, 1, 2
        check_load_above(3, 0, 2)
        # 4 -> Load 0, 1, 2, 3
        check_load_above(4, 0, 3)
        # 5 -> Load 4
        check_load_above(5, 4, 4)
        # 6 -> Load 4, 5
        check_load_above(6, 4, 5)
        # 7 -> Load 4, 5, 6
        check_load_above(7, 4, 6)
        # 8 -> Load 7
        check_load_above(8, 7, 7)
        # 9 -> Load 7, 8
        check_load_above(9, 7, 8)

    def test_load_paragraph_above_1(self):
        """ Checks that the method works when wrong indexes are passed. """
        # Paragraphs: {[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]}
        def check_wrong_above(s_id):
            data = load_paragraph_above(self.a1.id, s_id)
            self.check_keys_load(data)
            self.assertEquals(data['data'], [])
            self.assertEquals(data['first_sentence'], -1)
            self.assertEquals(data['last_sentence'], -1)

        check_wrong_above(-10)
        check_wrong_above(-1)
        check_wrong_above(10)
        check_wrong_above(100)

    def test_load_paragraph_below_0(self):
        """ Checks that the method works for all sentences. """
        # Paragraphs: {[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]}

        def check_load_below(sentence, first_sentence, last_sentence):
            data = load_paragraph_below(self.a1.id, sentence)
            self.check_keys_load(data)
            expected_tokens = []
            if first_sentence != -1:
                expected_tokens = TEST_ARTICLE['tokens'][first_sentence:last_sentence + 1]
                expected_tokens = [token for sentence_tokens in expected_tokens for token in sentence_tokens]
            self.assertEquals(data['data'], expected_tokens)
            self.assertEquals(data['first_sentence'], first_sentence)
            self.assertEquals(data['last_sentence'], last_sentence)

        # 0 -> 1, 2, 3
        check_load_below(0, 1, 3)
        # 1 -> 2, 3
        check_load_below(1, 2, 3)
        # 2 -> 3
        check_load_below(2, 3, 3)
        # 3 -> 4, 5, 6
        check_load_below(3, 4, 6)
        # 4 -> 5, 6
        check_load_below(4, 5, 6)
        # 5 -> 6
        check_load_below(5, 6, 6)
        # 6 -> 7, 8, 9
        check_load_below(6, 7, 9)
        # 7 -> 8, 9
        check_load_below(7, 8, 9)
        # 8 -> 9
        check_load_below(8, 9, 9)
        # 9 -> Nothing
        check_load_below(9, -1, -1)

    def test_load_paragraph_below_1(self):
        """ Checks that the method works when wrong indexes are passed. """
        # Paragraphs: {[0, 1, 2, 3], [4, 5, 6], [7, 8, 9]}
        def check_wrong_below(s_id):
            data = load_paragraph_below(self.a1.id, s_id)
            self.check_keys_load(data)
            self.assertEquals(data['data'], [])
            self.assertEquals(data['first_sentence'], -1)
            self.assertEquals(data['last_sentence'], -1)

        check_wrong_below(-10)
        check_wrong_below(-1)
        check_wrong_below(10)
        check_wrong_below(100)


class FrontendToPostgreTestCase(TestCase):

    def check_clean_keys(self, data):
        keys = list(data)
        self.assertEquals(len(keys), 3)
        self.assertTrue('index' in keys)
        self.assertTrue('labels' in keys)
        self.assertTrue('authors' in keys)

    def test_check_label_validity_0(self):
        """ Check that it works for valid labels """
        labels = 10 * [0]
        self.assertTrue(check_label_validity(labels))
        labels = 10 * [1]
        self.assertTrue(check_label_validity(labels))
        labels = [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
        self.assertTrue(check_label_validity(labels))
        labels = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1]
        self.assertTrue(check_label_validity(labels))
        labels = [0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0]
        self.assertTrue(check_label_validity(labels))
        labels = []
        self.assertTrue(check_label_validity(labels))

    def test_check_label_validity_1(self):
        """ Check that it works for invalid labels """
        labels = [2]
        self.assertFalse(check_label_validity(labels))
        labels = [-1]
        self.assertFalse(check_label_validity(labels))
        labels = 10 * [0] + [2]
        self.assertFalse(check_label_validity(labels))
        labels = 10 * [0] + [-1]
        self.assertFalse(check_label_validity(labels))
        labels = [2] + 10 * [0]
        self.assertFalse(check_label_validity(labels))
        labels = [-1] + 10 * [0]
        self.assertFalse(check_label_validity(labels))
        labels = 10 * [1] + [2]
        self.assertFalse(check_label_validity(labels))
        labels = 10 * [1] + [-1]
        self.assertFalse(check_label_validity(labels))
        labels = [1, 1, 1, 1, 1, 2, 0, 0, 0, 0, 0]
        self.assertFalse(check_label_validity(labels))
        labels = [0, 0, 0, 0, 2, 1, 1, 1, 1, 1, 1]
        self.assertFalse(check_label_validity(labels))
        labels = [1, 1, 1, 1, 1, -1, 0, 0, 0, 0, 0]
        self.assertFalse(check_label_validity(labels))
        labels = [0, 0, 0, 0, -1, 1, 1, 1, 1, 1, 1]
        self.assertFalse(check_label_validity(labels))
        labels = [0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1]
        self.assertFalse(check_label_validity(labels))
        labels = [1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0]
        self.assertFalse(check_label_validity(labels))
        labels = [1, 0, 1, 0, 0, 0]
        self.assertFalse(check_label_validity(labels))
        labels = [0, 0, 1, 0, 0, 1]
        self.assertFalse(check_label_validity(labels))
        labels = [1, 0, 0, 0, 0, 1]
        self.assertFalse(check_label_validity(labels))

    def test_clean_user_labels_0(self):
        """ Check that it works for a single sentence task and correct labels """

        def check_clean_simple(task_id, labels, authors, authors_absolute_index):
            data = clean_user_labels(TEST_ARTICLE['sentence_ends'], task_id, task_id[0], task_id[0], labels, authors)
            self.assertEquals(len(data), 1)
            cleaned = data[0]
            self.check_clean_keys(cleaned)
            self.assertEquals(cleaned['index'], task_id[0])
            self.assertEquals(cleaned['labels'], labels)
            self.assertEquals(cleaned['authors'], authors_absolute_index)

        # Check for no quote reported
        for i in range(10):
            check_clean_simple([i], len(TEST_ARTICLE['labels'][i]) * [0], [], [])

        # Check with the true labels, for the elements where the quote author is in the same sentence as the quote
        for i in [5, 9]:
            check_clean_simple([i], TEST_ARTICLE['labels'][i], TEST_ARTICLE['relative_authors'][i],
                               TEST_ARTICLE['authors'][i])

    def test_clean_user_labels_1(self):
        """ Check that it works for a single sentence task and wrong labels """

        def check_clean_wrong(task_id, labels, authors):
            data = clean_user_labels(TEST_ARTICLE['sentence_ends'], task_id, task_id[0], task_id[0], labels, authors)
            self.assertEquals(len(data), 0)

        # Check for wrong length of labels
        for i in range(10):
            check_clean_wrong([i], [1] + len(TEST_ARTICLE['labels'][i]) * [0], [0, 1])
            check_clean_wrong([i], (len(TEST_ARTICLE['labels'][i]) * [0])[:-1], [0, 1])
            check_clean_wrong([i], [0], [0, 1])

        # Check for labels with wrong values
        for i in range(10):
            check_clean_wrong([i], len(TEST_ARTICLE['labels'][i]) * [2], [0, 1])
            check_clean_wrong([i], len(TEST_ARTICLE['labels'][i]) * [-1], [0, 1])
            real_labels = TEST_ARTICLE['labels'][i].copy()
            real_labels[2] = 2
            check_clean_wrong([i], real_labels, [0, 1])
            real_labels = TEST_ARTICLE['labels'][i].copy()
            real_labels[2] = -1
            check_clean_wrong([i], real_labels, [0, 1])

        # Check for labels with wrong or no author values
        for i in range(10):
            loaded_length = len(TEST_ARTICLE['labels'][i])
            check_clean_wrong([i], TEST_ARTICLE['labels'][i], [loaded_length, loaded_length + 1])
            check_clean_wrong([i], TEST_ARTICLE['labels'][i], [-1, 0])
            check_clean_wrong([i], len(TEST_ARTICLE['labels'][i]) * [1], [])

    def test_clean_user_labels_2(self):
        """ Check that it works for a multiple sentence task and correctly formatted labels """

        def check_clean_two(task_ids, label1, label2, authors, authors_absolute_index):
            labels = label1 + label2
            data = clean_user_labels(TEST_ARTICLE['sentence_ends'], task_ids, task_ids[0], task_ids[1], labels, authors)
            self.assertEquals(len(data), 2)
            added_1 = data[0]
            added_2 = data[1]
            self.check_clean_keys(added_1)
            self.assertEquals(added_1['index'], task_ids[0])
            self.assertEquals(added_1['labels'], label1)
            self.assertEquals(added_1['authors'], authors_absolute_index)
            self.check_clean_keys(added_2)
            self.assertEquals(added_2['index'], task_ids[1])
            self.assertEquals(added_2['labels'], label2)
            self.assertEquals(added_2['authors'], authors_absolute_index)

        # Check for no quote reported
        for i in range(9):
            label1 = len(TEST_ARTICLE['labels'][i]) * [0]
            label2 = len(TEST_ARTICLE['labels'][i + 1]) * [0]
            check_clean_two([i, i+1], label1, label2, [], [])

        # Check for all quote reported
        for i in range(9):
            absolute_first_index = 0
            if i > 0:
                absolute_first_index = TEST_ARTICLE['sentence_ends'][i - 1] + 1
            relative_author_index = [2, 3, 4]
            absolute_author_index = [2 + absolute_first_index, 3 + absolute_first_index, 4 + absolute_first_index]
            label1 = len(TEST_ARTICLE['labels'][i]) * [1]
            label2 = len(TEST_ARTICLE['labels'][i + 1]) * [1]
            check_clean_two([i, i + 1], label1, label2, relative_author_index, absolute_author_index)

    def test_clean_user_labels_3(self):
        """ Check that it works for a single sentence task and an above load with
        only the original sentence containing the quote. """
        label1 = TEST_ARTICLE['labels'][2]
        label2 = TEST_ARTICLE['labels'][3]
        labels = label1 + label2
        absolute_authors = [24, 25]
        relative_authors = [0, 1]
        data = clean_user_labels(TEST_ARTICLE['sentence_ends'], [3], 2, 3, labels, relative_authors)
        self.assertEquals(len(data), 1)
        data = data[0]
        self.check_clean_keys(data)
        self.assertEquals(data['index'], 3)
        self.assertEquals(data['labels'], label2)
        self.assertEquals(data['authors'], absolute_authors)

    def test_clean_user_labels_4(self):
        """ Check that it works for a single sentence task and an above load with
        both sentences containing part of the quote. """
        label1 = len(TEST_ARTICLE['labels'][2]) * [0]
        label1[-1] = 1
        label2 = len(TEST_ARTICLE['labels'][3]) * [0]
        label2[0] = 1
        labels = label1 + label2
        relative_authors = [1, 2, 3]
        absolute_authors = [25, 26, 27]
        " As an extra sentence is loaded above it"
        data = clean_user_labels(TEST_ARTICLE['sentence_ends'], [3], 2, 3, labels, relative_authors)
        self.assertEquals(len(data), 2)
        added_1 = data[0]
        added_2 = data[1]
        self.check_clean_keys(added_1)
        self.assertEquals(added_1['index'], 3)
        self.assertEquals(added_1['labels'], label2)
        self.assertEquals(added_1['authors'], absolute_authors)
        self.check_clean_keys(added_2)
        self.assertEquals(added_2['index'], 2)
        self.assertEquals(added_2['labels'], label1)
        self.assertEquals(added_2['authors'], absolute_authors)

    def test_clean_user_labels_5(self):
        """ Check that it works for a single sentence task and two above loads with
        only the original sentence containing the quote. """
        label1 = TEST_ARTICLE['labels'][1]
        label2 = TEST_ARTICLE['labels'][2]
        label3 = TEST_ARTICLE['labels'][3]
        labels = label1 + label2 + label3
        absolute_authors = TEST_ARTICLE['authors'][3]
        relative_authors = TEST_ARTICLE['relative_authors'][3]
        " As an extra sentence is loaded above it"
        data = clean_user_labels(TEST_ARTICLE['sentence_ends'], [3], 1, 3, labels, relative_authors)
        self.assertEquals(len(data), 1)
        added_1 = data[0]
        self.check_clean_keys(added_1)
        self.assertEquals(added_1['index'], 3)
        self.assertEquals(added_1['labels'], label3)
        self.assertEquals(added_1['authors'], absolute_authors)

    def test_clean_user_labels_6(self):
        """ Check that it works for a single sentence task and a below load with
        only the original sentence containing the quote. """
        label1 = TEST_ARTICLE['labels'][0]
        label2 = TEST_ARTICLE['labels'][1]
        label3 = TEST_ARTICLE['labels'][2]
        labels = label1 + label2 + label3
        absolute_authors = TEST_ARTICLE['authors'][0]
        relative_authors = TEST_ARTICLE['relative_authors'][0]
        data = clean_user_labels(TEST_ARTICLE['sentence_ends'], [0], 0, 2, labels, relative_authors)
        self.assertEquals(len(data), 1)
        data = data[0]
        self.check_clean_keys(data)
        self.assertEquals(data['index'], 0)
        self.assertEquals(data['labels'], label1)
        self.assertEquals(data['authors'], absolute_authors)

    def test_clean_user_labels_7(self):
        """ Check that it works for a single sentence task and an below load with
        both sentences containing part of the quote. """
        label1 = len(TEST_ARTICLE['labels'][2]) * [0]
        label1[-1] = 1
        label2 = len(TEST_ARTICLE['labels'][3]) * [0]
        label2[0] = 1
        labels = label1 + label2
        relative_authors = [1, 2, 3]
        absolute_authors = [25, 26, 27]
        " As an extra sentence is loaded above it"
        data = clean_user_labels(TEST_ARTICLE['sentence_ends'], [2], 2, 3, labels, relative_authors)
        self.assertEquals(len(data), 2)
        added_1 = data[0]
        added_2 = data[1]
        self.check_clean_keys(added_1)
        self.assertEquals(added_1['index'], 2)
        self.assertEquals(added_1['labels'], label1)
        self.assertEquals(added_1['authors'], absolute_authors)
        self.check_clean_keys(added_2)
        self.assertEquals(added_2['index'], 3)
        self.assertEquals(added_2['labels'], label2)
        self.assertEquals(added_2['authors'], absolute_authors)
