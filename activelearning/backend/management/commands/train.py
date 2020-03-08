import csv
import numpy as np

from django.core.management.base import BaseCommand, CommandError

from backend.db_management import load_unlabeled_sentences
from backend.helpers import change_confidence
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
        parser.add_argument('--epochs', type=int, help='The maximum number of epochs to train for. Default: 500')
        parser.add_argument('--loss', help='The loss to use. Default: log.', choices=['log', 'hinge'])
        parser.add_argument('--penalty', help='The penalty to use. Default: l2.', choices=['l1', 'l2'])
        parser.add_argument('--regularization', type=float, help='The regularization term to use. Default: 0.01.')


    def handle(self, *args, **options):
        max_epochs = 500
        if options['epochs']:
            max_epochs = options['epochs']

        loss = 'log'
        if options['loss']:
            if options['loss'] == 'log':
                loss = 'log'
            elif options['loss'] == 'hinge':
                loss = 'hinge'

        penalty = 'l2'
        if options['penalty']:
            if options['penalty'] == 'l1':
                penalty = 'l1'
            elif options['penalty'] == 'l2':
                penalty = 'l2'

        alpha = 0.01
        if options['regularization']:
            alpha = options['regularization']

        try:
            print('Loading language model...')
            nlp = load_nlp()
            with open('data/cue_verbs.csv', 'r') as f:
                reader = csv.reader(f)
                cue_verbs = set(list(reader)[0])

            print('Training model...')
            trained_model = train_quote_detection(loss, penalty, alpha, max_epochs, nlp, cue_verbs)

            print('Evaluating all unlabeled quotes...')
            proba = loss == 'log'
            articles, sentences, in_quotes = load_unlabeled_sentences(nlp)
            max_hinge_value = 0.00001
            confidences = []
            predictions = []
            for article, article_sentences, article_in_quotes in zip(articles, sentences, in_quotes):
                probabilities = evaluate_unlabeled_sentences(trained_model, article_sentences, cue_verbs,
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

            print('Done')

        except IOError:
            raise CommandError('IO Error.')
