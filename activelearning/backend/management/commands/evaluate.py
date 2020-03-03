from django.core.management.base import BaseCommand, CommandError
import spacy
import csv
from backend.xml_parsing.helpers import load_nlp
from backend.ml.quote_detection import evaluate_quote_detection
from backend.ml.quote_attribution import evaluate_quote_attribution


def form_sentence(nlp, tokens):
    """  """
    sentence = ''.join(tokens)
    doc = nlp(sentence)
    return doc


class Command(BaseCommand):
    help = 'Evaluates the different models using cross validation.'

    def add_arguments(self, parser):
        parser.add_argument('--folds', type=int, help="The number of folds to perform cross-validation on.")

    def handle(self, *args, **options):
        folds = 5
        if options['folds']:
            folds = options['folds']

        try:
            print('\nLoading language model...')
            nlp = load_nlp()

            print('Loading cue verbs...')
            with open('data/cue_verbs.csv', 'r') as f:
                reader = csv.reader(f)
                cue_verbs = set(list(reader)[0])

            print('\n\nEvaluating quote detection...')
            evaluate_quote_detection(nlp, cue_verbs, cv_folds=folds)

            print('\n\nEvaluating one vs all quote attribution...')
            evaluate_quote_attribution(nlp, cue_verbs, cv_folds=folds, ovo=False)
            print('\n\nEvaluating one vs one quote attribution...')
            evaluate_quote_attribution(nlp, cue_verbs, cv_folds=folds, ovo=True)


        except IOError:
            raise CommandError('IO Error.')
