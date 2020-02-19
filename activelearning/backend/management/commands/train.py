from django.core.management.base import BaseCommand, CommandError

import spacy
import csv

from backend.db_management import load_sentence_labels, load_unlabeled_sentences
from backend.helpers import change_confidence
from backend.ml.quote_detection import train, predict_quotes


def set_custom_boundaries(doc):
    """ Custom boundaries so that spaCy doesn't split sentences at ';' or at '-[A-Z]'. """
    for token in doc[:-1]:
        if token.text == ";":
            doc[token.i+1].is_sent_start = False
        if token.text == "-" and token.i != 0:
            doc[token.i].is_sent_start = False
    return doc


def form_sentence(nlp, tokens):
    """  """
    sentence = ''.join(tokens)
    doc = nlp(sentence)
    return doc


class Command(BaseCommand):
    help = 'Trains the model with all fully annotated articles.'

    def add_arguments(self, parser):
        parser.add_argument('model', help="Model to train. One of {'L1 logistic', 'L2 logistic', 'Linear SVC'}")

    def handle(self, *args, **options):
        model = options['model']
        try:
            print('Loading language model...')
            nlp = spacy.load('fr_core_news_md')
            nlp.add_pipe(set_custom_boundaries, before="parser")

            print('Extracting labeled articles...')
            train_sentences, train_labels, train_in_quotes, _, _, _ = load_sentence_labels(nlp)

            print('Loading cue verbs...')
            with open('../data/cue_verbs.csv', 'r') as f:
                reader = csv.reader(f)
                cue_verbs = set(list(reader)[0])

            print('Training model...')
            trained_model = train(model, train_sentences, train_labels, cue_verbs, train_in_quotes)

            print('Evaluating all unlabeled quotes...')
            articles, sentences, in_quotes = load_unlabeled_sentences(nlp)
            for article, sentences in zip(articles, sentences):
                probabilities = predict_quotes(trained_model, sentences, cue_verbs, in_quotes)
                # Map the probability that a sentence is a quote to a confidence:
                #   * probability is 0.5: model has no clue, confidence 0
                #   * probability is 0 or 1: model knows, confidence 1
                confidence = [2 * abs(0.5 - prob) for prob in probabilities]
                # For sentences in the article that are fully labeled, the confidence is 1
                new_confidences = [max(label, conf) for label, conf in zip(article.labeled['labeled'], confidence)]
                change_confidence(article.id, new_confidences)

            print('Done')

        except IOError:
            raise CommandError('IO Error.')
