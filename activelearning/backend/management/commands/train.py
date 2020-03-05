import csv

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
        parser.add_argument('model', help="Model to train. One of {'L1 logistic', 'L2 logistic', 'Linear SVC'}")

    def handle(self, *args, **options):
        model = options['model']
        try:
            print('Loading language model...')
            nlp = load_nlp()
            with open('data/cue_verbs.csv', 'r') as f:
                reader = csv.reader(f)
                cue_verbs = set(list(reader)[0])

            print('Training model...')
            trained_model = train_quote_detection(nlp, cue_verbs)

            print('Evaluating all unlabeled quotes...')
            articles, sentences, in_quotes = load_unlabeled_sentences(nlp)
            for article, sentences in zip(articles, sentences):
                probabilities = evaluate_unlabeled_sentences(trained_model, sentences, cue_verbs, in_quotes)
                # Map the probability that a sentence is a quote to a confidence:
                #   * probability is 0.5: model has no clue, confidence 0
                #   * probability is 0 or 1: model knows, confidence 1
                confidence = [2 * abs(0.5 - prob) for prob in probabilities]
                prediction = [round(prob) for prob in probabilities]
                # For sentences in the article that are fully labeled, the confidence is 1
                new_confidences = [max(label, conf) for label, conf in zip(article.labeled['labeled'], confidence)]
                change_confidence(article.id, new_confidences, prediction)

            print('Done')

        except IOError:
            raise CommandError('IO Error.')
