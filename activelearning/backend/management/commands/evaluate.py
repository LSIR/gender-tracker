from django.core.management.base import BaseCommand, CommandError

import csv
from backend.xml_parsing.helpers import load_nlp
from backend.ml.baseline import baseline_quote_detection, baseline_quote_attribution
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
            print()
            print('Loading language model...'.ljust(80), end='\r')
            nlp = load_nlp()

            print('Loading cue verbs...'.ljust(80), end='\r')
            with open('data/cue_verbs.csv', 'r') as f:
                reader = csv.reader(f)
                cue_verbs = set(list(reader)[0])

            alphas = [0.01, 0.1]
            losses = ['log', 'hinge']
            log_penalties = ['l1', 'l2']

            print('Evaluating quote detection...'.ljust(80), end='\r')

            print('\n  Baseline:')
            results = baseline_quote_detection(nlp)
            print(results.average_score())

            for l in losses:
                for p in log_penalties:
                    print(f'\n  {p} {l}:')
                    for alpha in alphas:
                        print(f'\n    Evaluating with regularization term: {alpha}')
                        train_res, test_res = evaluate_quote_detection(l, p, alpha, nlp, cue_verbs, cv_folds=folds)
                        print(f'    Average Training Results\n{train_res.average_score()}')
                        print(f'    Average Test Results\n{test_res.average_score()}')

            print('\n\nEvaluating quote attribution...')
            print('\n  Baseline:')
            baseline_quote_attribution(nlp, cue_verbs)
            print('\n  L1 Logistic One vs All:')
            evaluate_quote_attribution('l1', nlp, cue_verbs, cv_folds=folds, ovo=False)
            print('\n  L2 Logistic One vs All:')
            evaluate_quote_attribution('l2', nlp, cue_verbs, cv_folds=folds, ovo=False)
            print('\n  L1 Logistic One vs One:')
            evaluate_quote_attribution('l1', nlp, cue_verbs, cv_folds=folds, ovo=True)
            print('\n  L2 Logistic One vs One:')
            evaluate_quote_attribution('l2', nlp, cue_verbs, cv_folds=folds, ovo=True)

        except IOError:
            raise CommandError('IO Error.')
