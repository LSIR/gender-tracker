from django.test import TestCase
from django.test import Client

from backend.models import Article, UserLabel
from backend.db_management import add_article_to_db
from backend.helpers import label_consensus, change_confidence
from backend.xml_parsing.postgre_to_xml import database_to_xml

import spacy
import json


def set_custom_boundaries(doc):
    """
    Custom boundaries so that spaCy doesn't split sentences at ';' or at '-[A-Z]'.
    """
    for token in doc[:-1]:
        if token.text == ";":
            doc[token.i+1].is_sent_start = False
        if token.text == "-" and token.i != 0:
            doc[token.i].is_sent_start = False
    return doc


""" The language model. """
nlp = spacy.load('fr_core_news_md')
nlp.add_pipe(set_custom_boundaries, before="parser")


""" The content and annotation of the first article. """
TEST_1 = {
    'input_xml': '<?xml version="1.0"?>\n'
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
    'output_xml': '<?xml version="1.0"?>\n'
                  '<article>\n'
                  '\t<titre>Le football</titre>\n'
                  '\t<p><RS a="0">Le fameux joueur de football Diego Maradona est meilleur que Lionel Messi</RS>. Du '
                  'moins, c\'est ce que pense <author a="0">Serge Aurier</author>. Il l\'affirme dans un interview '
                  'avec L\'Equipe. Il pense que <RS a="0">sa victoire en coupe du monde est plus importante que les '
                  'victoires individuelles de lutin du FC Barcelone</RS>.</p>\n'
                  '\t<p>Il ne pense pas que Messi pourra un jour gagner une coupe du monde. Mais <author a="1">Platini '
                  '</author>nous informe qu\'en fait <RS a="1">c\'est lui "le meilleur joueur du monde"</RS>. Et que '
                  '"<RS a="1">ça n\'a rien à voir avec son ego</RS>".</p>\n'
                  '\t<p>Mais au final, c\'est vraiement Wayne Rooney, le meilleur joueur de tous les temps. C\'est '
                  'indiscutable. Même <author a="2">Zlatan </author>le dit: "<RS a="2">Personne n\'est meilleur que '
                  'Wayne</RS>".</p>\n'
                  '</article>',
    'text': 'Le fameux joueur de football Diego Maradona est meilleur que Lionel Messi. Du moins, c\'est ce que pense '
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
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        # 13 - 23
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 24 - 33
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 34 - 55
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
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
    'sentence_ends': [12, 23, 33, 55, 70, 88, 102, 120, 124, 138],
    'paragraph_ends': [3, 6, 9],
    'look_above_index': [3, 6],
    'look_below_index': [0],
    'double_loads': [],
}


""" The content and annotation of the second article. """
TEST_2 = {
    'input_xml': '<?xml version="1.0"?>\n'
                '<article>\n'
                '\t<titre>Article sans sens.</titre>\n'
                '\t<p>Cet article est utilisé pour tester l\'implémentation du gender tracker. Une citation "est bien '
                'plus importante que la véracité des dires", répond Pierre. Michel Schmid ne dit rien. Il criait '
                'pourtant plus tôt que "rien n\'est mieux qu\'un code bien commenté".</p>\n'
                '\t<p>Alain est d\'un avis différent. Pour lui, les tests sont la partie la plus importante du code. Il'
                ' pense que c\'est plus important que le reste.</p>\n'
                '</article>',
    'output_xml': '<?xml version="1.0"?>\n'
                  '<article>\n'
                  '\t<titre>Article sans sens.</titre>\n'
                  '\t<p>Cet article est utilisé pour tester l\'implémentation du gender tracker. Une citation "<RS '
                  'a="0">est bien plus importante que la véracité des dires</RS>", répond <author a="0">Pierre</author>'
                  '. <author a="1">Michel Schmid </author>ne dit rien. Il criait '
                  'pourtant plus tôt que "<RS a="1">rien n\'est mieux qu\'un code bien commenté</RS>".</p>\n'
                  '\t<p><author a="2">Alain </author>est d\'un avis différent. Pour lui, <RS a="2">les tests sont la '
                  'partie la plus importante du code</RS>. Il pense que <RS a="2">c\'est plus important que le reste'
                  '</RS>.</p>\n'
                  '</article>',
    'text': 'Cet article est utilisé pour tester l\'implémentation du gender tracker. Une citation "est bien plus '
            'importante que la véracité des dires", répond Pierre. Michel Schmid ne dit rien. Il criait pourtant plus '
            'tôt que "rien n\'est mieux qu\'un code bien commenté". Alain est d\'un avis différent. Pour lui, les tests'
            ' sont la partie la plus importante du code. Il pense que c\'est plus important que le reste.',
    'tokens': [
        ['Cet ', 'article ', 'est ', 'utilisé ', 'pour ', 'tester ', "l'", 'implémentation ', 'du ', 'gender ',
         'tracker', '. '],
        ['Une ', 'citation ', '"', 'est ', 'bien ', 'plus ', 'importante ', 'que ', 'la ', 'véracité ', 'des ', 'dires',
         '"', ', ', 'répond ', 'Pierre', '. '],
        ['Michel ', 'Schmid ', 'ne ', 'dit ', 'rien', '. '],
        ['Il ', 'criait ', 'pourtant ', 'plus ', 'tôt ', 'que ', '"', 'rien ', "n'", 'est ', 'mieux ', "qu'", 'un ',
         'code ', 'bien ', 'commenté', '"', '.'],
        ['Alain ', 'est ', "d'", 'un ', 'avis ', 'différent', '. '],
        ['Pour ', 'lui', ', ', 'les ', 'tests ', 'sont ', 'la ', 'partie ', 'la ', 'plus ', 'importante ', 'du ',
         'code', '. '],
        ['Il ', 'pense ', 'que ', "c'", 'est ', 'plus ', 'important ', 'que ', 'le ', 'reste', '.']
    ],
    'in_quotes': [
        # 0 - 11
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 12 - 28
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
        # 29 - 34
        [0, 0, 0, 0, 0, 0],
        # 35 - 52
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        # 53 - 59
        [0, 0, 0, 0, 0, 0, 0],
        # 60 - 73
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 74 - 84
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
    'labels': [
        # 0 - 11
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        # 12 - 28
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
        # 29 - 34
        [0, 0, 0, 0, 0, 0],
        # 35 - 52
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        # 53 - 59
        [0, 0, 0, 0, 0, 0, 0],
        # 60 - 73
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        # 74 - 84
        [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0],
    ],
    'authors': [
        [],
        [27],
        [],
        [29, 30],
        [],
        [53],
        [53]
    ],
    'sentence_ends': [11, 28, 34, 52, 59, 73, 84],
    'paragraph_ends': [3, 6],
    'look_above_index': [3, 5, 6],
    'look_below_index': [],
    'double_loads': [],
}


""" The content and annotations of a short third article, containing a 2-sentence quote. """
TEST_3 = {
    'input_xml': '<?xml version="1.0"?>\n'
                 '<article>\n'
                 '\t<titre>Double.</titre>\n'
                 '\t<p>Pierre-Alain est content. Il dit: "Je suis heureux. Je n\'ai plus faim".</p>\n'
                 '\t<p>Son ami Pablo ne l\'est pas. Il nous explique. Je n\'ai pas assez mangé. Pierre-Alain ne m\'en '
                 'a pas laissé assez.</p>\n'
                 '</article>',
    'output_xml': '<?xml version="1.0"?>\n'
                  '<article>\n'
                  '\t<titre>Double.</titre>\n'
                  '\t<p><author a="0">Pierre-Alain </author>est content. Il dit: "<RS a="0">Je suis heureux. Je n\'ai '
                  'plus faim</RS>".</p>\n'
                  '\t<p>Son ami <author a="1">Pablo </author>ne l\'est pas. Il nous explique. <RS a="1">Je n\'ai pas '
                  'assez mangé. Pierre-Alain ne m\'en a pas laissé assez.</RS></p>\n'
                  '</article>',
    'text': 'Pierre-Alain est content. Il dit: "Je suis heureux. Je n\'ai plus faim". Son ami Pablo ne l\'est pas. '
            'Il nous explique. Je n\'ai pas assez mangé. Pierre-Alain ne m\'en a pas laissé assez.',
    'tokens': [
        ['Pierre', '-', 'Alain ', 'est ', 'content', '. '],
        ['Il ', 'dit', ': ', '"', 'Je ', 'suis ', 'heureux', '. '],
        ['Je ', 'n\'', 'ai ', 'plus ', 'faim', '"', '.'],
        ['Son ', 'ami ', 'Pablo ', 'ne ', 'l\'', 'est ', 'pas', '. '],
        ['Il ', 'nous ', 'explique', '. '],
        ['Je ', 'n\'', 'ai ', 'pas ', 'assez ', 'mangé', '. '],
        ['Pierre', '-', 'Alain ', 'ne ', 'm\'', 'en ', 'a ', 'pas ', 'laissé ', 'assez', '.']
    ],
    'in_quotes': [
        # 0 - 5
        [0, 0, 0, 0, 0, 0],
        # 6 - 13
        [0, 0, 0, 0, 1, 1, 1, 1],
        # 14 - 20
        [1, 1, 1, 1, 1, 0, 0],
        # 21 - 28
        [0, 0, 0, 0, 0, 0, 0, 0],
        # 29 - 32
        [0, 0, 0, 0],
        # 33 - 39
        [0, 0, 0, 0, 0, 0, 0],
        # 40 - 50
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
    'labels': [
        # 0 - 5
        [0, 0, 0, 0, 0, 0],
        # 6 - 13
        [0, 0, 0, 0, 1, 1, 1, 1],
        # 14 - 20
        [1, 1, 1, 1, 1, 0, 0],
        # 21 - 28
        [0, 0, 0, 0, 0, 0, 0, 0],
        # 29 - 32
        [0, 0, 0, 0],
        # 33 - 39
        [1, 1, 1, 1, 1, 1, 1],
        # 40 - 50
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
    'authors': [
        [],
        [0, 1, 2],
        [0, 1, 2],
        [],
        [],
        [23],
        [23]
    ],
    'relative_authors': [
        [],
        [0, 1, 2],
        [0, 1, 2],
        [],
        [],
        [2],
        [2]
    ],
    'sentence_ends': [5, 13, 20, 28, 32, 39, 50],
    'paragraph_ends': [2, 6],
    'look_above_index': [1, 2, 5, 6],
    'look_below_index': [],
    'double_loads': [1],
}


def load_new_task(test_class, client):
    """
    Loads a new sentence from the database.

    :param test_class: django.test.TestCase
        The test class.
    :param client: django.test.Client
        The client that is loading the sentence.
    :return: int, int, list(int), list(string), string.
        * The unique session id of the user
        * The id of the article from which the task is loaded.
        * The list of sentences to annotate.
        * The list of tokens in these sentences.
        * One of {sentence, paragraph, None, error}. The task to perform
    """
    response = client.get('/api/loadContent/')
    user_id = client.session['id']
    data = json.loads(response.content)
    keys = list(data)
    test_class.assertEquals(len(keys), 5)
    test_class.assertTrue('article_id' in keys)
    test_class.assertTrue('sentence_id' in keys)
    test_class.assertTrue('data' in keys)
    test_class.assertTrue('task' in keys)
    test_class.assertTrue('admin' in keys)
    article_id = data['article_id']
    sentence_ids = data['sentence_id']
    text = data['data']
    task = data['task']
    return user_id, article_id, sentence_ids, text, task


def submit_task(test_class, client, article_id, sentence_ids, first_sentence, last_sentence, tags, authors, task):
    """
    Submits the user labels with the given parameters and checks that they are correctly saved to the database.

    :param test_class: django.test.TestCase
        The test class.
    :param client: django.test.Client
        The client that is loading the sentence.
    :param article_id: int
        The id of the article in the database.
    :param sentence_ids: list(int)
        The ids of the sentences for which the annotation was the task.
    :param first_sentence: int
        The smallest id of a sentence loaded by the user. Equal to sentence_id[0] if and only if the user didn't load
        any text above, otherwise smaller than sentence_id[0].
    :param last_sentence: int
        The largest id of a sentence loaded by the user. Equal to sentence_id[-1] if and only if the user didn't load
        any text below, otherwise larger than sentence_id[-1].
    :param tags: list(int)
        The labels the user gave to each token.
    :param authors: list(int)
        The indices of tokens that are the author of the quote, if there was one.
    :param task: string
        The task the user performed. One of {'sentence', 'paragraph'}.
    """
    data = {
        'article_id': article_id,
        'sentence_id': sentence_ids,
        'first_sentence': first_sentence,
        'last_sentence': last_sentence,
        'tags': tags,
        'authors': authors,
        'task': task,
    }
    response = client.post('/api/submitTags/', data, content_type='application/json')
    data_out = json.loads(response.content)
    keys = list(data_out)
    test_class.assertEquals(len(keys), 1)
    test_class.assertTrue('success' in keys)
    test_class.assertTrue(data_out['success'])


def parse_extra_load(test_class, response):
    """
    Checks that the response from a load of extra text is in the correct format and extracts information from it.

    :param test_class: django.test.TestCase
        The test class.
    :param response: django.http.JsonResponse
        The response from the backend.
    :return: list(string), int, int.
        * The list of extra tokens loaded.
        * The index of the first sentence loaded.
        * The index of the last sentence loaded.
    """
    data = json.loads(response.content)
    keys = list(data)
    test_class.assertEquals(len(keys), 4)
    test_class.assertTrue('data' in keys)
    test_class.assertTrue('first_sentence' in keys)
    test_class.assertTrue('last_sentence' in keys)
    test_class.assertTrue('Success' in keys)
    test_class.assertTrue(data['Success'])
    text = data['data']
    first_sentence = data['first_sentence']
    last_sentence = data['last_sentence']
    return text, first_sentence, last_sentence


def load_above(test_class, client, article_id, first_sentence):
    """
    Loads the paragraph above the sentence with index first_sentence. If first_sentence is the first sentence in a
    paragraph, loads all the sentences in the paragraph above it. If it isn't, loads the remaining sentences in that
    paragraph.

    :param test_class: django.test.TestCase
        The test class.
    :param client: django.test.Client
        The client that is loading the sentence.
    :param article_id: int
        The id of the article in the database.
    :param first_sentence: int.
        The index of the sentence above which we want the content.
    :return: list(string), int, int.
        * The list of extra tokens loaded.
        * The index of the first sentence loaded.
        * The index of the last sentence loaded.
    """
    data = {
        'article_id': article_id,
        'first_sentence': first_sentence,
    }
    response = client.get('/api/loadAbove/', data, content_type='application/json')
    return parse_extra_load(test_class, response)


def load_below(test_class, client, article_id, last_sentence):
    """
    Loads the paragraph below the sentence with index last_sentence. If last_sentence is the last sentence in a
    paragraph, loads all the sentences in the paragraph below it. If it isn't, loads the remaining sentences in that
    paragraph.

    :param test_class: django.test.TestCase
        The test class.
    :param client: django.test.Client
        The client that is loading the sentence.
    :param article_id: int
        The id of the article in the database.
    :param last_sentence: int.
        The index of the sentence below which we want the content.
    :return: list(string), int, int.
        * The list of extra tokens loaded.
        * The index of the first sentence loaded.
        * The index of the last sentence loaded.
    """
    data = {
        'article_id': article_id,
        'last_sentence': last_sentence,
    }
    response = client.get('/api/loadBelow/', data, content_type='application/json')
    return parse_extra_load(test_class, response)


def relative_author_positions(authors, first_sentence_id, sentence_ends):
    """
    Computes the relative index of authors when given their index in the full document.

    :param authors: list(int)
        The indices of the authors in the full document.
    :param first_sentence_id: int
        The index of the first sentence loaded by the user.
    :param sentence_ends: list(int)
        The index of the last token of each sentence.
    :return: list(int)
        The index of the author tokens with respect to the first token in the loaded text.
    """
    first_token_index = 0
    if first_sentence_id > 0:
        first_token_index = sentence_ends[first_sentence_id - 1] + 1
    relative_authors = []
    for a in authors:
        relative_authors.append(a - first_token_index)
    return relative_authors


def check_annotations(test_class, article, num_sentences, expected_num_labels, expected_text, expected_consensus):
    """
    Checks that the labels stored represent the correct representation of the article.

    :param test_class: TestCase
        The class doing the testing.
    :param article: backend.models.Article
        The article for which labels need to be checked.
    :param num_sentences: int
        The number of sentences in the article.
    :param expected_num_labels:
        The expected number of user labels per sentence.
    :param expected_text: string
        The expected output XML string.
    :param expected_consensus: float
        The expected consensus among user labels
    """
    labels = []
    authors = []
    for s_id in range(num_sentences):
        sentence_labels = UserLabel.objects.filter(article=article, sentence_index=s_id)
        valid_sentence_labels = sentence_labels.exclude(labels__labels=[])
        all_labels = [label.labels['labels'] for label in valid_sentence_labels]
        all_authors = [label.author_index['author_index'] for label in valid_sentence_labels]
        test_class.assertEquals(len(all_labels), expected_num_labels)
        test_class.assertEquals(len(all_authors), expected_num_labels)
        sent_label, sent_authors, consensus = label_consensus(all_labels, all_authors)
        labels.append(sent_label)
        authors.append(sent_authors)
        test_class.assertEquals(consensus, expected_consensus)

    xml_string = database_to_xml(article, labels, authors)
    test_class.assertEquals(xml_string, expected_text)


def check_task_done(test_class, clients):
    """
    Check that no more sentences are left to annotate.

    :param test_class: TestCase
        The class doing the testing.
    :param clients: list(django.test.Client)
        The clients that can annotate sentences
    """
    for c in clients:
        user_id, article_id, sentence_ids, text, task = load_new_task(test_class, c)
        test_class.assertEquals(article_id, -1)
        test_class.assertEquals(sentence_ids, [])
        test_class.assertEquals(text, [])
        test_class.assertEquals(task, 'None')


def make_admin(test_class, client):
    """
    Makes a client an admin in the system.

    :param test_class: TestCase
        The class doing the testing.
    :param client: django.test.Client
        The client to make an admin.
    """
    response = client.get('/api/admin_tagger/', {'key': 'i_want_to_be_admin'})
    data = json.loads(response.content)
    test_class.assertTrue(data['Success'])
    test_class.assertTrue(client.session['admin'])


def check_sentence_skipped(test_class, article, sentence_id, user_id):
    """ Check that a sentence was skipped by a user. """
    user_labels = UserLabel.objects.filter(article=article, sentence_index=sentence_id, session_id=user_id)
    test_class.assertEquals(len(user_labels), 1)
    # Only keep valid user labels, of which there should be none
    user_labels = user_labels.exclude(labels__labels=[])
    test_class.assertEquals(len(user_labels), 0)


class SingleUserTestCase(TestCase):
    """ Case where a single user is annotating sentences """

    def setUp(self):
        # Add an article to the database
        self.a1 = add_article_to_db('../data/test_article_1.xml', nlp, 'Heidi.News')
        self.a2 = add_article_to_db('../data/test_article_2.xml', nlp, 'Heidi.News')
        self.a3 = add_article_to_db('../data/test_article_3.xml', nlp, 'Heidi.News')

    def test_0_loading(self):
        """
        Test that the XML files are correctly loaded and stored in the database.
        """
        def check_article(article, name, data):
            self.assertEquals(article.name, name)
            self.assertEquals(article.text, data['input_xml'])
            self.assertEquals(article.tokens['tokens'], [token for sentence_tokens in data['tokens']
                                                         for token in sentence_tokens])
            self.assertEquals(article.sentences['sentences'], data['sentence_ends'])
            self.assertEquals(article.paragraphs['paragraphs'], data['paragraph_ends'])
            self.assertEquals(article.labeled['labeled'], len(data['sentence_ends']) * [0])
            self.assertEquals(article.in_quotes['in_quotes'], [in_quote for sentence_in_quote in data['in_quotes']
                                                               for in_quote in sentence_in_quote])
            self.assertEquals(article.confidence['confidence'], len(data['sentence_ends']) * [0])
            self.assertEquals(article.confidence['min_confidence'], 0)
            self.assertEquals(article.admin_article, False)

        check_article(self.a1, 'Le football', TEST_1)
        check_article(self.a2, 'Article sans sens.', TEST_2)
        check_article(self.a3, 'Double.', TEST_3)

    def test_1_trivial(self):
        """
        Test where the user simply annotates all sentences as text that isn't reported, without ever loading extra text.
        """
        # Define a new client
        c = Client()
        make_admin(self, c)

        test_1_sentences = 10
        test_2_sentences = 7
        test_3_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_2['id'] = self.a2.id
        TEST_3['id'] = self.a3.id

        def annotate_simple(num_sentences, true_values):
            s_id = 0
            while s_id < num_sentences:
                sentence_tasks = [s_id]
                tokens = true_values['tokens'][s_id].copy()
                first_sentence = s_id
                last_sentence = s_id
                if s_id in true_values['double_loads']:
                    s_id += 1
                    sentence_tasks += [s_id]
                    tokens += true_values['tokens'][s_id].copy()
                    last_sentence = s_id
                user_id, article_id, sentence_ids, text, task = load_new_task(self, c)
                self.assertEquals(article_id, true_values['id'])
                self.assertEquals(sentence_ids, sentence_tasks)
                self.assertEquals(text, tokens)
                self.assertEquals(task, 'sentence')
                submit_task(self, c, article_id, sentence_tasks, first_sentence, last_sentence,
                            len(text) * [0], [], task)
                s_id += 1

        # The first article should be loaded first as it has a smaller index
        annotate_simple(test_1_sentences, TEST_1)
        annotate_simple(test_2_sentences, TEST_2)
        annotate_simple(test_3_sentences, TEST_3)

        check_task_done(self, [c])
        check_annotations(self, self.a1, test_1_sentences, 1, TEST_1['input_xml'], 1)
        check_annotations(self, self.a2, test_2_sentences, 1, TEST_2['input_xml'], 1)
        check_annotations(self, self.a3, test_3_sentences, 1, TEST_3['input_xml'], 1)

    def test_2_real_annotations(self):
        """
        Test where a single user annotates all sentences correctly, looking up in the text when needed.
        """
        # Define a new client
        c = Client()
        make_admin(self, c)
        test_1_sentences = 10
        test_2_sentences = 7
        test_3_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_2['id'] = self.a2.id
        TEST_3['id'] = self.a3.id

        def annotate_true(num_sentences, true_values):
            s_id = 0
            while s_id < num_sentences:
                sentence_tasks = [s_id]
                tokens = true_values['tokens'][s_id].copy()
                labels = true_values['labels'][s_id].copy()
                first_sentence = s_id
                last_sentence = s_id
                if s_id in true_values['double_loads']:
                    s_id += 1
                    sentence_tasks += [s_id]
                    tokens += true_values['tokens'][s_id].copy()
                    labels += true_values['labels'][s_id].copy()
                    last_sentence = s_id

                user_id, article_id, sentence_ids, text, task = load_new_task(self, c)

                self.assertEquals(article_id, true_values['id'])
                self.assertEquals(sentence_ids, sentence_tasks)
                self.assertEquals(text, tokens)
                self.assertEquals(task, 'sentence')

                if s_id in true_values['look_above_index']:
                    extra_text, first_extra, last_extra = load_above(self, c, article_id, first_sentence)
                    extra_labels = []
                    for e_id in range(first_extra, last_extra + 1):
                        # As we are not currently annotating the next sentnce but simply looking for the author,
                        # the new tokens are labeled as 0
                        extra_labels += len(true_values['labels'][e_id]) * [0]
                    first_sentence = min(first_sentence, first_extra)
                    labels = extra_labels + labels

                if s_id in true_values['look_below_index']:
                    extra_text, first_extra, last_extra = load_below(self, c, article_id, last_sentence)
                    extra_labels = []
                    for e_id in range(first_extra, last_extra + 1):
                        # As we are not currently annotating the next sentnce but simply looking for the author,
                        # the new tokens are labeled as 0
                        extra_labels += len(true_values['labels'][e_id]) * [0]
                    labels = labels + extra_labels
                    last_sentence = max(last_sentence, last_extra)

                authors = true_values['authors'][s_id].copy()
                authors = relative_author_positions(authors, first_sentence, true_values['sentence_ends'].copy())
                submit_task(self, c, article_id, sentence_tasks, first_sentence, last_sentence, labels, authors, task)
                s_id += 1

        # The first article should be loaded first as it has a smaller index
        annotate_true(test_1_sentences, TEST_1)
        annotate_true(test_2_sentences, TEST_2)
        annotate_true(test_3_sentences, TEST_3)

        check_task_done(self, [c])
        check_annotations(self, self.a1, test_1_sentences, 1, TEST_1['output_xml'], 1)
        check_annotations(self, self.a2, test_2_sentences, 1, TEST_2['output_xml'], 1)
        check_annotations(self, self.a3, test_3_sentences, 1, TEST_3['output_xml'], 1)

    def test_3_with_paragraphs(self):
        """
        Test where a single user annotates all sentences correctly, looking up in the text when needed. Some text is
        first given as paragraphs. It has to be reloaded as sentences as it contains quotes.
        """
        # Change the confidences on sentences of the second paragraph so that it is loaded as a whole paragraph.
        new_confidence = self.a1.confidence['confidence'].copy()
        new_confidence[4:7] = [100, 100, 100]
        change_confidence(self.a1.id, new_confidence)
        # Define a new client
        c = Client()
        make_admin(self, c)
        test_1_sentences = 10
        test_2_sentences = 7
        test_3_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_2['id'] = self.a2.id
        TEST_3['id'] = self.a3.id

        def annotate_true(num_sentences, true_values):
            s_id = 0
            paragraph_seen = False
            while s_id < num_sentences:
                user_id, article_id, sentence_ids, text, task = load_new_task(self, c)

                # The first time sentence 4 is seen, it should be loaded as the full paragraph
                # The sentence index isn't increased, as each sentence then needs to be tagged by the user.
                if task == 'paragraph':
                    paragraph_seen = True
                    self.assertEquals(s_id, 4)
                    self.assertEquals(article_id, true_values['id'])
                    self.assertEquals(sentence_ids, [4, 5, 6])
                    tokens = true_values['tokens'][4] + true_values['tokens'][5] + true_values['tokens'][6]
                    self.assertEquals(text, tokens)
                    self.assertEquals(task, 'paragraph')
                    submit_task(self, c, article_id, sentence_ids, 4, 6, len(tokens) * [1], [], task)
                else:
                    sentence_tasks = [s_id]
                    tokens = true_values['tokens'][s_id].copy()
                    labels = true_values['labels'][s_id].copy()
                    first_sentence = s_id
                    last_sentence = s_id
                    if s_id in true_values['double_loads']:
                        s_id += 1
                        sentence_tasks += [s_id]
                        tokens += true_values['tokens'][s_id].copy()
                        labels += true_values['labels'][s_id].copy()
                        last_sentence = s_id

                    self.assertEquals(article_id, true_values['id'])
                    self.assertEquals(sentence_ids, sentence_tasks)
                    self.assertEquals(text, tokens)
                    self.assertEquals(task, 'sentence')

                    if s_id in true_values['look_above_index']:
                        extra_text, first_extra, last_extra = load_above(self, c, article_id, first_sentence)
                        extra_labels = []
                        for id in range(first_extra, last_extra + 1):
                            # As we are not currently annotating the next sentence but simply looking for the author,
                            # the new tokens are labeled as 0
                            extra_labels += len(true_values['labels'][id]) * [0]
                        first_sentence = min(first_sentence, first_extra)
                        labels = extra_labels + labels

                    if s_id in true_values['look_below_index']:
                        extra_text, first_extra, last_extra = load_below(self, c, article_id, last_sentence)
                        extra_labels = []
                        for id in range(first_extra, last_extra + 1):
                            # As we are not currently annotating the next sentnce but simply looking for the author,
                            # the new tokens are labeled as 0
                            extra_labels += len(true_values['labels'][id]) * [0]
                        labels = labels + extra_labels
                        last_sentence = max(last_sentence, last_extra)

                    authors = true_values['authors'][s_id]
                    authors = relative_author_positions(authors, first_sentence, true_values['sentence_ends'])
                    submit_task(self, c, article_id, sentence_ids, first_sentence, last_sentence, labels, authors, task)
                    s_id += 1
            return paragraph_seen

        # The first article should be loaded first as it has a smaller index
        paragraph_seen = annotate_true(test_1_sentences, TEST_1)
        self.assertTrue(paragraph_seen)
        paragraph_seen = annotate_true(test_2_sentences, TEST_2)
        self.assertFalse(paragraph_seen)
        paragraph_seen = annotate_true(test_3_sentences, TEST_3)
        self.assertFalse(paragraph_seen)

        check_task_done(self, [c])
        check_annotations(self, self.a1, test_1_sentences, 1, TEST_1['output_xml'], 1)
        check_annotations(self, self.a2, test_2_sentences, 1, TEST_2['output_xml'], 1)
        check_annotations(self, self.a3, test_3_sentences, 1, TEST_3['output_xml'], 1)

    def test_4_skip_sentence(self):
        """ Tests that an admin user can skip all sentences. """
        # Define a new client
        c = Client()
        make_admin(self, c)

        test_1_sentences = 10
        test_2_sentences = 7
        test_3_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_2['id'] = self.a2.id
        TEST_3['id'] = self.a3.id

        def skip_sentences(num_sentences, true_values):
            s_id = 0
            while s_id < num_sentences:
                sentence_tasks = [s_id]
                tokens = true_values['tokens'][s_id].copy()
                first_sentence = s_id
                last_sentence = s_id
                if s_id in true_values['double_loads']:
                    s_id += 1
                    sentence_tasks += [s_id]
                    tokens += true_values['tokens'][s_id].copy()
                    last_sentence = s_id
                user_id, article_id, sentence_ids, text, task = load_new_task(self, c)
                self.assertEquals(article_id, true_values['id'])
                self.assertEquals(sentence_ids, sentence_tasks)
                self.assertEquals(text, tokens)
                self.assertEquals(task, 'sentence')
                submit_task(self, c, article_id, sentence_tasks, first_sentence, last_sentence, [], [], task)
                s_id += 1

        # The first article should be loaded first as it has a smaller index
        skip_sentences(test_1_sentences, TEST_1)
        skip_sentences(test_2_sentences, TEST_2)
        skip_sentences(test_3_sentences, TEST_3)

        def check_all_skipped(article, num_sentences, user_id):
            for s_id in range(num_sentences):
                check_sentence_skipped(self, article, s_id, user_id)

        user_id = c.session['id']
        check_task_done(self, [c])
        check_all_skipped(self.a1, test_1_sentences, user_id)
        check_all_skipped(self.a2, test_2_sentences, user_id)
        check_all_skipped(self.a3, test_3_sentences, user_id)


class TwoUserAdminTestCase(TestCase):
    """ Case where a two admin users are annotating sentences """

    def setUp(self):
        # Add an article to the database
        self.a1 = add_article_to_db('../data/test_article_1.xml', nlp, 'Heidi.News')
        self.a2 = add_article_to_db('../data/test_article_2.xml', nlp, 'Heidi.News')
        self.a3 = add_article_to_db('../data/test_article_3.xml', nlp, 'Heidi.News')

    def test_1_admin_trivial(self):
        """
        Test where two admin users simply annotates all sentences as text that isn't reported, without ever loading
        extra text. The two users each annotate some of the sentences.

        This shouldn't change the annotation flow at all, as only a single admin label is required for a sentence to be
        annotated.
        """
        # Define two clients
        c1 = Client()
        c2 = Client()
        make_admin(self, c1)
        make_admin(self, c2)
        # The ids of the sentences the first client annotates
        client_1_sentences = [0, 4, 5, 6]

        test_1_sentences = 10
        test_2_sentences = 7
        test_3_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_2['id'] = self.a2.id
        TEST_3['id'] = self.a3.id

        def annotate_simple(num_sentences, true_values):
            s_id = 0
            while s_id < num_sentences:
                if s_id in client_1_sentences:
                    c = c1
                else:
                    c = c2
                sentence_tasks = [s_id]
                tokens = true_values['tokens'][s_id].copy()
                first_sentence = s_id
                last_sentence = s_id
                if s_id in true_values['double_loads']:
                    s_id += 1
                    sentence_tasks += [s_id]
                    tokens += true_values['tokens'][s_id].copy()
                    last_sentence = s_id
                user_id, article_id, sentence_ids, text, task = load_new_task(self, c)
                self.assertEquals(article_id, true_values['id'])
                self.assertEquals(sentence_ids, sentence_tasks)
                self.assertEquals(text, tokens)
                self.assertEquals(task, 'sentence')
                submit_task(self, c, article_id, sentence_tasks, first_sentence, last_sentence,
                            len(text) * [0], [], task)
                s_id += 1

        # The first article should be loaded first as it has a smaller index
        annotate_simple(test_1_sentences, TEST_1)
        annotate_simple(test_2_sentences, TEST_2)
        annotate_simple(test_3_sentences, TEST_3)

        check_task_done(self, [c1, c2])
        check_annotations(self, self.a1, test_1_sentences, 1, TEST_1['input_xml'], 1)
        check_annotations(self, self.a2, test_2_sentences, 1, TEST_2['input_xml'], 1)
        check_annotations(self, self.a3, test_3_sentences, 1, TEST_3['input_xml'], 1)

    def test_2_admin_real_annotations(self):
        """
        Test where a two admin user annotates all sentences correctly, looking up in the text when needed. The two
        users each annotate some of the sentences.

        This shouldn't change the annotation flow at all, as only a single admin label is required for a sentence to be
        annotated.
        """
        # Define two clients
        c1 = Client()
        c2 = Client()
        make_admin(self, c1)
        make_admin(self, c2)
        # The ids of the sentences the first client annotates
        client_1_sentences = [0, 4, 5, 6]

        test_1_sentences = 10
        test_2_sentences = 7
        test_3_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_2['id'] = self.a2.id
        TEST_3['id'] = self.a3.id

        def annotate_true(num_sentences, true_values):
            s_id = 0
            while s_id < num_sentences:
                if s_id in client_1_sentences:
                    c = c1
                else:
                    c = c2
                sentence_tasks = [s_id]
                tokens = true_values['tokens'][s_id].copy()
                labels = true_values['labels'][s_id].copy()
                first_sentence = s_id
                last_sentence = s_id
                if s_id in true_values['double_loads']:
                    s_id += 1
                    sentence_tasks += [s_id]
                    tokens += true_values['tokens'][s_id].copy()
                    labels += true_values['labels'][s_id].copy()
                    last_sentence = s_id

                user_id, article_id, sentence_ids, text, task = load_new_task(self, c)

                self.assertEquals(article_id, true_values['id'])
                self.assertEquals(sentence_ids, sentence_tasks)
                self.assertEquals(text, tokens)
                self.assertEquals(task, 'sentence')

                if s_id in true_values['look_above_index']:
                    extra_text, first_extra, last_extra = load_above(self, c, article_id, first_sentence)
                    extra_labels = []
                    for e_id in range(first_extra, last_extra + 1):
                        # As we are not currently annotating the next sentnce but simply looking for the author,
                        # the new tokens are labeled as 0
                        extra_labels += len(true_values['labels'][e_id]) * [0]
                    first_sentence = min(first_sentence, first_extra)
                    labels = extra_labels + labels

                if s_id in true_values['look_below_index']:
                    extra_text, first_extra, last_extra = load_below(self, c, article_id, last_sentence)
                    extra_labels = []
                    for e_id in range(first_extra, last_extra + 1):
                        # As we are not currently annotating the next sentnce but simply looking for the author,
                        # the new tokens are labeled as 0
                        extra_labels += len(true_values['labels'][e_id]) * [0]
                    labels = labels + extra_labels
                    last_sentence = max(last_sentence, last_extra)

                authors = true_values['authors'][s_id].copy()
                authors = relative_author_positions(authors, first_sentence, true_values['sentence_ends'].copy())
                submit_task(self, c, article_id, sentence_tasks, first_sentence, last_sentence, labels, authors, task)
                s_id += 1

        # The first article should be loaded first as it has a smaller index
        annotate_true(test_1_sentences, TEST_1)
        annotate_true(test_2_sentences, TEST_2)
        annotate_true(test_3_sentences, TEST_3)

        check_task_done(self, [c1, c2])
        check_annotations(self, self.a1, test_1_sentences, 1, TEST_1['output_xml'], 1)
        check_annotations(self, self.a2, test_2_sentences, 1, TEST_2['output_xml'], 1)
        check_annotations(self, self.a3, test_3_sentences, 1, TEST_3['output_xml'], 1)

    def test_3_admin_with_paragraphs(self):
        """
        Test where a single user annotates all sentences correctly, looking up in the text when needed. Some text is
        first given as paragraphs. It has to be reloaded as sentences as it contains quotes.
        """
        # Change the confidences on sentences of the second paragraph so that it is loaded as a whole paragraph.
        new_confidence = self.a1.confidence['confidence'].copy()
        new_confidence[4:7] = [100, 100, 100]
        change_confidence(self.a1.id, new_confidence)

        # Define two clients
        c1 = Client()
        c2 = Client()
        make_admin(self, c1)
        make_admin(self, c2)
        # The ids of the sentences the first client annotates
        client_1_sentences = [0, 4, 5, 6]

        test_1_sentences = 10
        test_2_sentences = 7
        test_3_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_2['id'] = self.a2.id
        TEST_3['id'] = self.a3.id

        def annotate_true(num_sentences, true_values):
            s_id = 0
            paragraph_seen = False
            while s_id < num_sentences:
                if s_id in client_1_sentences:
                    c = c1
                else:
                    c = c2

                user_id, article_id, sentence_ids, text, task = load_new_task(self, c)

                # The first time sentence 4 is seen, it should be loaded as the full paragraph
                # The sentence index isn't increased, as each sentence then needs to be tagged by the user.
                if task == 'paragraph':
                    paragraph_seen = True
                    self.assertEquals(s_id, 4)
                    self.assertEquals(article_id, true_values['id'])
                    self.assertEquals(sentence_ids, [4, 5, 6])
                    tokens = true_values['tokens'][4] + true_values['tokens'][5] + true_values['tokens'][6]
                    self.assertEquals(text, tokens)
                    self.assertEquals(task, 'paragraph')
                    submit_task(self, c, article_id, sentence_ids, 4, 6, len(tokens) * [1], [], task)
                else:
                    sentence_tasks = [s_id]
                    tokens = true_values['tokens'][s_id].copy()
                    labels = true_values['labels'][s_id].copy()
                    first_sentence = s_id
                    last_sentence = s_id
                    if s_id in true_values['double_loads']:
                        s_id += 1
                        sentence_tasks += [s_id]
                        tokens += true_values['tokens'][s_id].copy()
                        labels += true_values['labels'][s_id].copy()
                        last_sentence = s_id

                    self.assertEquals(article_id, true_values['id'])
                    self.assertEquals(sentence_ids, sentence_tasks)
                    self.assertEquals(text, tokens)
                    self.assertEquals(task, 'sentence')

                    if s_id in true_values['look_above_index']:
                        extra_text, first_extra, last_extra = load_above(self, c, article_id, first_sentence)
                        extra_labels = []
                        for id in range(first_extra, last_extra + 1):
                            # As we are not currently annotating the next sentence but simply looking for the author,
                            # the new tokens are labeled as 0
                            extra_labels += len(true_values['labels'][id]) * [0]
                        first_sentence = min(first_sentence, first_extra)
                        labels = extra_labels + labels

                    if s_id in true_values['look_below_index']:
                        extra_text, first_extra, last_extra = load_below(self, c, article_id, last_sentence)
                        extra_labels = []
                        for id in range(first_extra, last_extra + 1):
                            # As we are not currently annotating the next sentnce but simply looking for the author,
                            # the new tokens are labeled as 0
                            extra_labels += len(true_values['labels'][id]) * [0]
                        labels = labels + extra_labels
                        last_sentence = max(last_sentence, last_extra)

                    authors = true_values['authors'][s_id]
                    authors = relative_author_positions(authors, first_sentence, true_values['sentence_ends'])
                    submit_task(self, c, article_id, sentence_ids, first_sentence, last_sentence, labels, authors, task)
                    s_id += 1
            return paragraph_seen

        # The first article should be loaded first as it has a smaller index
        paragraph_seen = annotate_true(test_1_sentences, TEST_1)
        self.assertTrue(paragraph_seen)
        paragraph_seen = annotate_true(test_2_sentences, TEST_2)
        self.assertFalse(paragraph_seen)
        paragraph_seen = annotate_true(test_3_sentences, TEST_3)
        self.assertFalse(paragraph_seen)

        check_task_done(self, [c1, c2])
        check_annotations(self, self.a1, test_1_sentences, 1, TEST_1['output_xml'], 1)
        check_annotations(self, self.a2, test_2_sentences, 1, TEST_2['output_xml'], 1)
        check_annotations(self, self.a3, test_3_sentences, 1, TEST_3['output_xml'], 1)

    def test_4_admin_one_skip_one_annotate(self):
        """
        Test where a admin single user skips all sentences, while another annotates them all correctly, looking up in
        the text when needed. The user that doesn't know shouldn't impact the sentences the one who does sees.
        """
        # Define two clients
        c1 = Client()
        c2 = Client()
        make_admin(self, c1)
        make_admin(self, c2)
        # The ids of the sentences the first client annotates
        client_1_sentences = [0, 4, 5, 6]

        test_1_sentences = 10
        test_2_sentences = 7
        test_3_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_2['id'] = self.a2.id
        TEST_3['id'] = self.a3.id

        def annotate_true(num_sentences, true_values):
            s_id = 0
            while s_id < num_sentences:
                sentence_tasks = [s_id]
                tokens = true_values['tokens'][s_id].copy()
                labels = true_values['labels'][s_id].copy()
                first_sentence = s_id
                last_sentence = s_id
                if s_id in true_values['double_loads']:
                    s_id += 1
                    sentence_tasks += [s_id]
                    tokens += true_values['tokens'][s_id].copy()
                    labels += true_values['labels'][s_id].copy()
                    last_sentence = s_id

                # First user loads task, doesn't know the answer
                user_id, article_id, sentence_ids, text, task = load_new_task(self, c1)

                self.assertEquals(article_id, true_values['id'])
                self.assertEquals(sentence_ids, sentence_tasks)
                self.assertEquals(text, tokens)
                self.assertEquals(task, 'sentence')

                if s_id in true_values['look_above_index']:
                    _, _, _ = load_above(self, c1, article_id, first_sentence)

                if s_id in true_values['look_below_index']:
                    _, _, _  = load_below(self, c1, article_id, last_sentence)

                submit_task(self, c1, article_id, sentence_tasks, first_sentence, last_sentence, [], [], task)

                # Second user loads task, knows the answer
                user_id, article_id, sentence_ids, text, task = load_new_task(self, c2)

                self.assertEquals(article_id, true_values['id'])
                self.assertEquals(sentence_ids, sentence_tasks)
                self.assertEquals(text, tokens)
                self.assertEquals(task, 'sentence')

                if s_id in true_values['look_above_index']:
                    extra_text, first_extra, last_extra = load_above(self, c2, article_id, first_sentence)
                    extra_labels = []
                    for e_id in range(first_extra, last_extra + 1):
                        # As we are not currently annotating the next sentence but simply looking for the author,
                        # the new tokens are labeled as 0
                        extra_labels += len(true_values['labels'][e_id]) * [0]
                    first_sentence = min(first_sentence, first_extra)
                    labels = extra_labels + labels

                if s_id in true_values['look_below_index']:
                    extra_text, first_extra, last_extra = load_below(self, c2, article_id, last_sentence)
                    extra_labels = []
                    for e_id in range(first_extra, last_extra + 1):
                        # As we are not currently annotating the next sentnce but simply looking for the author,
                        # the new tokens are labeled as 0
                        extra_labels += len(true_values['labels'][e_id]) * [0]
                    labels = labels + extra_labels
                    last_sentence = max(last_sentence, last_extra)

                authors = true_values['authors'][s_id].copy()
                authors = relative_author_positions(authors, first_sentence, true_values['sentence_ends'].copy())
                submit_task(self, c2, article_id, sentence_tasks, first_sentence, last_sentence, labels, authors, task)
                s_id += 1

        # The first article should be loaded first as it has a smaller index
        annotate_true(test_1_sentences, TEST_1)
        annotate_true(test_2_sentences, TEST_2)
        annotate_true(test_3_sentences, TEST_3)

        # Check that the first use has skipped all sentences

        def check_all_skipped(article, num_sentences, user_id):
            for s_id in range(num_sentences):
                check_sentence_skipped(self, article, s_id, user_id)

        user_id = c1.session['id']
        check_task_done(self, [c1])
        check_all_skipped(self.a1, test_1_sentences, user_id)
        check_all_skipped(self.a2, test_2_sentences, user_id)
        check_all_skipped(self.a3, test_3_sentences, user_id)

        check_task_done(self, [c2])
        check_annotations(self, self.a1, test_1_sentences, 1, TEST_1['output_xml'], 1)
        check_annotations(self, self.a2, test_2_sentences, 1, TEST_2['output_xml'], 1)
        check_annotations(self, self.a3, test_3_sentences, 1, TEST_3['output_xml'], 1)


class FourUserTestCase(TestCase):
    """ Case where four normal users are annotating sentences """

    def setUp(self):
        # Add an article to the database
        self.a1 = add_article_to_db('../data/test_article_1.xml', nlp, 'Heidi.News')
        self.a2 = add_article_to_db('../data/test_article_2.xml', nlp, 'Heidi.News')
        self.a3 = add_article_to_db('../data/test_article_3.xml', nlp, 'Heidi.News')

    def test_1_trivial(self):
        """
        Test where four users all sentences as text that isn't reported, without ever loading extra text. All users need
        to annotate all sentences, as they are not admin users.
        """
        # Define the clients
        c1 = Client()
        c2 = Client()
        c3 = Client()
        c4 = Client()

        test_1_sentences = 10
        test_2_sentences = 7
        test_3_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_2['id'] = self.a2.id
        TEST_3['id'] = self.a3.id

        def annotate_simple(num_sentences, true_values, c):
            s_id = 0
            while s_id < num_sentences:
                sentence_tasks = [s_id]
                tokens = true_values['tokens'][s_id].copy()
                first_sentence = s_id
                last_sentence = s_id
                if s_id in true_values['double_loads']:
                    s_id += 1
                    sentence_tasks += [s_id]
                    tokens += true_values['tokens'][s_id].copy()
                    last_sentence = s_id
                user_id, article_id, sentence_ids, text, task = load_new_task(self, c)
                self.assertEquals(article_id, true_values['id'])
                self.assertEquals(sentence_ids, sentence_tasks)
                self.assertEquals(text, tokens)
                self.assertEquals(task, 'sentence')
                submit_task(self, c, article_id, sentence_tasks, first_sentence, last_sentence,
                            len(text) * [0], [], task)
                s_id += 1

        # The first article should be loaded first as it has a smaller index
        for c in [c1, c2, c3, c4]:
            annotate_simple(test_1_sentences, TEST_1, c)
            annotate_simple(test_2_sentences, TEST_2, c)
            annotate_simple(test_3_sentences, TEST_3, c)

        check_task_done(self, [c1, c2, c3, c4])
        check_annotations(self, self.a1, test_1_sentences, 4, TEST_1['input_xml'], 1)
        check_annotations(self, self.a2, test_2_sentences, 4, TEST_2['input_xml'], 1)
        check_annotations(self, self.a3, test_3_sentences, 4, TEST_3['input_xml'], 1)

    def test_2_real_annotations(self):
        """
        Test where all users annotate all sentences correctly, looking up in the text when needed. All users annotate
        all sentences, as they are not admin users.
        """
        # Define the clients
        c1 = Client()
        c2 = Client()
        c3 = Client()
        c4 = Client()

        test_1_sentences = 10
        test_2_sentences = 7
        test_3_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_2['id'] = self.a2.id
        TEST_3['id'] = self.a3.id

        def annotate_true(num_sentences, true_values, c):
            s_id = 0
            while s_id < num_sentences:
                sentence_tasks = [s_id]
                tokens = true_values['tokens'][s_id].copy()
                labels = true_values['labels'][s_id].copy()
                first_sentence = s_id
                last_sentence = s_id
                if s_id in true_values['double_loads']:
                    s_id += 1
                    sentence_tasks += [s_id]
                    tokens += true_values['tokens'][s_id].copy()
                    labels += true_values['labels'][s_id].copy()
                    last_sentence = s_id

                user_id, article_id, sentence_ids, text, task = load_new_task(self, c)

                self.assertEquals(article_id, true_values['id'])
                self.assertEquals(sentence_ids, sentence_tasks)
                self.assertEquals(text, tokens)
                self.assertEquals(task, 'sentence')

                if s_id in true_values['look_above_index']:
                    extra_text, first_extra, last_extra = load_above(self, c, article_id, first_sentence)
                    extra_labels = []
                    for e_id in range(first_extra, last_extra + 1):
                        # As we are not currently annotating the next sentnce but simply looking for the author,
                        # the new tokens are labeled as 0
                        extra_labels += len(true_values['labels'][e_id]) * [0]
                    first_sentence = min(first_sentence, first_extra)
                    labels = extra_labels + labels

                if s_id in true_values['look_below_index']:
                    extra_text, first_extra, last_extra = load_below(self, c, article_id, last_sentence)
                    extra_labels = []
                    for e_id in range(first_extra, last_extra + 1):
                        # As we are not currently annotating the next sentnce but simply looking for the author,
                        # the new tokens are labeled as 0
                        extra_labels += len(true_values['labels'][e_id]) * [0]
                    labels = labels + extra_labels
                    last_sentence = max(last_sentence, last_extra)

                authors = true_values['authors'][s_id].copy()
                authors = relative_author_positions(authors, first_sentence, true_values['sentence_ends'].copy())
                submit_task(self, c, article_id, sentence_tasks, first_sentence, last_sentence, labels, authors, task)
                s_id += 1

        # The first article should be loaded first as it has a smaller index
        for c in [c1, c2, c3, c4]:
            annotate_true(test_1_sentences, TEST_1, c)
            annotate_true(test_2_sentences, TEST_2, c)
            annotate_true(test_3_sentences, TEST_3, c)

        check_task_done(self, [c1, c2, c3, c4])
        check_annotations(self, self.a1, test_1_sentences, 4, TEST_1['output_xml'], 1)
        check_annotations(self, self.a2, test_2_sentences, 4, TEST_2['output_xml'], 1)
        check_annotations(self, self.a3, test_3_sentences, 4, TEST_3['output_xml'], 1)

    def test_3_with_paragraphs(self):
        """
        Test where a single user annotates all sentences correctly, looking up in the text when needed. Some text is
        first given as paragraphs. It has to be reloaded as sentences as it contains quotes.
        """
        # Change the confidences on sentences of the second paragraph so that it is loaded as a whole paragraph.
        new_confidence = self.a1.confidence['confidence'].copy()
        new_confidence[4:7] = [100, 100, 100]
        change_confidence(self.a1.id, new_confidence)

        # Define the clients
        c1 = Client()
        c2 = Client()
        c3 = Client()
        c4 = Client()
        # The ids of the sentences the first client annotates
        client_1_sentences = [0, 4, 5, 6]

        test_1_sentences = 10
        test_2_sentences = 7
        test_3_sentences = 7

        TEST_1['id'] = self.a1.id
        TEST_2['id'] = self.a2.id
        TEST_3['id'] = self.a3.id

        def annotate_true(num_sentences, true_values, c):
            s_id = 0
            paragraph_seen = False
            while s_id < num_sentences:
                user_id, article_id, sentence_ids, text, task = load_new_task(self, c)

                # The first time sentence 4 is seen, it should be loaded as the full paragraph
                # The sentence index isn't increased, as each sentence then needs to be tagged by the user.
                if task == 'paragraph':
                    paragraph_seen = True
                    self.assertEquals(s_id, 4)
                    self.assertEquals(article_id, true_values['id'])
                    self.assertEquals(sentence_ids, [4, 5, 6])
                    tokens = true_values['tokens'][4] + true_values['tokens'][5] + true_values['tokens'][6]
                    self.assertEquals(text, tokens)
                    self.assertEquals(task, 'paragraph')
                    submit_task(self, c, article_id, sentence_ids, 4, 6, len(tokens) * [1], [], task)
                else:
                    sentence_tasks = [s_id]
                    tokens = true_values['tokens'][s_id].copy()
                    labels = true_values['labels'][s_id].copy()
                    first_sentence = s_id
                    last_sentence = s_id
                    if s_id in true_values['double_loads']:
                        s_id += 1
                        sentence_tasks += [s_id]
                        tokens += true_values['tokens'][s_id].copy()
                        labels += true_values['labels'][s_id].copy()
                        last_sentence = s_id

                    self.assertEquals(article_id, true_values['id'])
                    self.assertEquals(sentence_ids, sentence_tasks)
                    self.assertEquals(text, tokens)
                    self.assertEquals(task, 'sentence')

                    if s_id in true_values['look_above_index']:
                        extra_text, first_extra, last_extra = load_above(self, c, article_id, first_sentence)
                        extra_labels = []
                        for id in range(first_extra, last_extra + 1):
                            # As we are not currently annotating the next sentence but simply looking for the author,
                            # the new tokens are labeled as 0
                            extra_labels += len(true_values['labels'][id]) * [0]
                        first_sentence = min(first_sentence, first_extra)
                        labels = extra_labels + labels

                    if s_id in true_values['look_below_index']:
                        extra_text, first_extra, last_extra = load_below(self, c, article_id, last_sentence)
                        extra_labels = []
                        for id in range(first_extra, last_extra + 1):
                            # As we are not currently annotating the next sentnce but simply looking for the author,
                            # the new tokens are labeled as 0
                            extra_labels += len(true_values['labels'][id]) * [0]
                        labels = labels + extra_labels
                        last_sentence = max(last_sentence, last_extra)

                    authors = true_values['authors'][s_id]
                    authors = relative_author_positions(authors, first_sentence, true_values['sentence_ends'])
                    submit_task(self, c, article_id, sentence_ids, first_sentence, last_sentence, labels, authors, task)
                    s_id += 1
            return paragraph_seen

        # The first article should be loaded first as it has a smaller index
        for c in [c1, c2, c3, c4]:
            # The first article should be loaded first as it has a smaller index
            paragraph_seen = annotate_true(test_1_sentences, TEST_1, c)
            if c == c1:
                self.assertTrue(paragraph_seen)
            else:
                self.assertFalse(paragraph_seen)
            paragraph_seen = annotate_true(test_2_sentences, TEST_2, c)
            self.assertFalse(paragraph_seen)
            paragraph_seen = annotate_true(test_3_sentences, TEST_3, c)
            self.assertFalse(paragraph_seen)

        check_task_done(self, [c1, c2, c3, c4])
        check_annotations(self, self.a1, test_1_sentences, 4, TEST_1['output_xml'], 1)
        check_annotations(self, self.a2, test_2_sentences, 4, TEST_2['output_xml'], 1)
        check_annotations(self, self.a3, test_3_sentences, 4, TEST_3['output_xml'], 1)
