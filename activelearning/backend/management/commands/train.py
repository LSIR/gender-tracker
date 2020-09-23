import csv
import numpy as np

from django.core.management.base import BaseCommand, CommandError

from backend.db_management import load_unlabeled_sentences
from backend.extraction_pipeline import path_quote_detection_weights, path_author_attribution_weights, \
    author_prediction_poly_degree, quote_detection_poly_degree
from backend.helpers import change_confidence
from backend.ml.author_prediction import evaluate_author_prediction_test
from backend.ml.helpers import save_model
from backend.ml.quote_detection import train_quote_detection, evaluate_unlabeled_sentences
from backend.xml_parsing.helpers import load_nlp


def form_sentence(nlp, tokens):
    """  """
    sentence = ''.join(tokens)
    doc = nlp(sentence)
    return doc


class Command(BaseCommand):
    help = 'Trains the model with all fully annotated articles.'

    def add_arguments(self, parser):
        parser.add_argument('--epochs', type=int, help='Max number of epochs to train for. Default: 500', default=500)

        parser.add_argument('--qd_loss', help='The loss to use for quote detection. Default: log',
                            choices=['log', 'hinge'], default='log')
        parser.add_argument('--qd_penalty', help='The penalty to use for quote detection. Default: l2',
                            choices=['l1', 'l2'], default='l2')
        parser.add_argument('--qd_reg', type=float, help='Reg to use for quote detection. Default: 0.01',
                            default=0.01)

        parser.add_argument('--ap_loss', help='The loss to use for author prediction. Default: hinge',
                            choices=['log', 'hinge'], default='hinge')
        parser.add_argument('--ap_penalty', help='The penalty to use for author prediction. Default: l1',
                            choices=['l1', 'l2'], default='l1')
        parser.add_argument('--ap_reg', type=float, help='Reg to use for author prediction. Default: 0.01',
                            default=0.01)

    def handle(self, *args, **options):
        max_epochs = options['epochs']
        qd_loss = options['qd_loss']
        qd_penalty = options['qd_penalty']
        qd_alpha = options['qd_reg']

        ap_loss = options['ap_loss']
        ap_penalty = options['ap_penalty']
        ap_alpha = options['ap_reg']

        try:
            print('\nLoading language model...\n')
            nlp = load_nlp()
            with open('data/cue_verbs.csv', 'r') as f:
                reader = csv.reader(f)
                cue_verbs = set(list(reader)[0])

            print('Training quote detection...')
            qd_ed = quote_detection_poly_degree
            qd_trained_model = train_quote_detection(qd_loss, qd_penalty, qd_alpha, max_epochs, nlp, cue_verbs, qd_ed)
            save_model(qd_trained_model, path_quote_detection_weights)
            print(f'Saved trained model at {path_quote_detection_weights}\n')

            print("Training author prediction...")
            ap_ed = author_prediction_poly_degree
            ap_trained_model, _, _, _, _, _ =\
                evaluate_author_prediction_test(ap_loss, ap_penalty, ap_alpha, max_epochs, nlp, cue_verbs, ap_ed)
            save_model(ap_trained_model, path_author_attribution_weights)
            print(f'Saved trained model at {path_quote_detection_weights}\n')

            print('Evaluating all unlabeled quotes...')
            proba = qd_loss == 'log'
            articles, sentences, in_quotes = load_unlabeled_sentences(nlp)
            max_hinge_value = 0.00001
            confidences = []
            predictions = []
            for article, article_sentences, article_in_quotes in zip(articles, sentences, in_quotes):
                probabilities = evaluate_unlabeled_sentences(qd_trained_model, article_sentences, cue_verbs,
                                                             article_in_quotes, proba=proba)
                if proba:
                    # Map the probability that a sentence is a quote to a confidence:
                    #   * probability is 0.5: model has no clue, confidence 0
                    #   * probability is 0 or 1: model knows, confidence 1
                    confidence = [2 * abs(0.5 - prob) for prob in probabilities]
                    confidences.append(confidence)
                    prediction = [round(prob) for prob in probabilities]
                    predictions.append(prediction)
                else:
                    # When using hinge loss, the confidence is the distance to the seperating hyperplane
                    # Take the log to reduce the effect of very large values
                    confidence = [np.log(abs(prob)) for prob in probabilities]
                    confidences.append(confidence)
                    prediction = [int(prob > 0) for prob in probabilities]
                    predictions.append(prediction)
                    max_hinge_value = max(max_hinge_value, max(confidence))

            for article, confidence, prediction in zip(articles, confidences, predictions):
                if not proba:
                    confidence = [conf/max_hinge_value for conf in confidence]
                # For sentences in the article that are fully labeled, the confidence is 1
                new_confidences = [max(label, conf) for label, conf in zip(article.labeled['labeled'], confidence)]
                change_confidence(article.id, new_confidences, prediction)

            print('Done\n')

        except IOError:
            raise
            raise CommandError('IO Error.')
