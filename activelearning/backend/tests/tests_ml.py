from django.test import TestCase
from django.test import Client

from backend.models import Article
from backend.helpers import change_confidence
from backend.db_management import add_article_to_db, add_user_label_to_db,\
    load_sentence_labels, load_unlabeled_sentences
from backend.ml.quote_detection import evaluate_classifiers, train, predict_quotes

import spacy
import csv


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


def add_correct_labels(test_article, test_article_id):
    """
    Adds a correctly annotated label to each sentence in the article

    :param test_article:
    :return:
    """
    for index, (labels, authors) in enumerate(zip(test_article['labels'], test_article['authors'])):
        add_user_label_to_db(0000, test_article_id, index, labels, authors, True)


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


class QuoteDetectionTestCase(TestCase):
    """ Case where a single user is annotating sentences """

    def setUp(self):
        # Add an article to the database
        self.a1 = add_article_to_db('../data/test_article_1.xml', nlp)
        self.a2 = add_article_to_db('../data/test_article_2.xml', nlp)
        self.a3 = add_article_to_db('../data/test_article_3.xml', nlp)

    def test_0_evaluate_models(self):
        """ Tests that the different models can be trained and their performance printed. Need to set only 2-fold cross-
         validation for the test to pass. """
        add_correct_labels(TEST_1, self.a1.id)
        add_correct_labels(TEST_2, self.a2.id)
        add_correct_labels(TEST_3, self.a3.id)

        print('\n\n\nTest 0\n')
        train_sentences, train_labels, test_sentences, test_labels = load_sentence_labels(nlp)
        print(f'\nTraining Examples: {len(train_sentences)}')
        print(f'Training Quotes: {sum(train_labels)}\n')
        print(f'Test Examples: {len(test_sentences)}')
        print(f'Test Quotes: {sum(test_labels)}\n')

        print('Loading cue verbs...')
        with open('../data/cue_verbs.csv', 'r') as f:
            reader = csv.reader(f)
            cue_verbs = set(list(reader)[0])

        print('Evaluating different models...')
        model_scores = evaluate_classifiers(train_sentences, train_labels, cue_verbs, cv_folds=2)
        for name, score in model_scores.items():
            print(f'\n\nModel: {name}\n'
                  f'\tAccuracy:  {score["test_accuracy"]}\n'
                  f'\tPrecision: {score["test_precision_macro"]}\n'
                  f'\tF1:        {score["test_f1_macro"]}\n')
        print('\nFinished Test 0\n\n\n')

    def test_1_train_model(self):
        """ """
        add_correct_labels(TEST_1, self.a1.id)
        add_correct_labels(TEST_2, self.a2.id)

        print('\n\n\nTest 1\n')
        train_sentences, train_labels, test_sentences, test_labels = load_sentence_labels(nlp)
        print(f'\nTraining Examples: {len(train_sentences)}')
        print(f'Training Quotes: {sum(train_labels)}\n')
        print(f'Test Examples: {len(test_sentences)}')
        print(f'Test Quotes: {sum(test_labels)}\n')

        print('Loading cue verbs...')
        with open('../data/cue_verbs.csv', 'r') as f:
            reader = csv.reader(f)
            cue_verbs = set(list(reader)[0])

        models = ['L1 logistic', 'L2 logistic', 'Linear SVC']
        for m in models:
            print(f'\nTraining model {m}')
            trained_model = train(m, train_sentences, train_labels, cue_verbs)
            print(f'\nComputing new confidences')
            articles, sentences = load_unlabeled_sentences(nlp)
            for article, article_sentences in zip(articles, sentences):
                probabilities = predict_quotes(trained_model, article_sentences, cue_verbs)[:, 1]
                # Map the probability that a sentence is a quote to a confidence:
                #   * probability is 0.5: model has no clue, confidence 0
                #   * probability is 0 or 1: model knows, confidence 1
                confidence = [2 * abs(0.5 - prob) for prob in probabilities]
                print('Probabilties:', list(probabilities))
                print('Confidence:', confidence)
                print('Labeled', list(article.labeled['labeled']))
                # For sentences in the article that are fully labeled, the confidence is 1
                new_confidences = [max(label, conf) for label, conf in zip(article.labeled['labeled'], confidence)]
                print('New Confidence', new_confidences)
                conf = change_confidence(article.id, new_confidences)
            article_3 = Article.objects.get(id=self.a3.id)
            print(f'\nConfidences for article 3: {article_3.confidence["confidence"]}\n'
                  f'Minimum Confidence: {conf}\n')

        print('\nFinished Test 1\n\n\n')