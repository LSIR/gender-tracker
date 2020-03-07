import csv
import itertools

from django.core.management.base import BaseCommand, CommandError

from backend.ml.baseline import baseline_quote_detection, baseline_quote_attribution
from backend.ml.quote_attribution import evaluate_quote_attribution
from backend.ml.quote_detection import evaluate_quote_detection
from backend.ml.scoring import ResultAccumulator
from backend.xml_parsing.helpers import load_nlp


def form_sentence(nlp, tokens):
    """  """
    sentence = ''.join(tokens)
    doc = nlp(sentence)
    return doc


def pretty_print(train, test):
    print(f'        Average Training Results\n{train["results"].print_average_score()}\n'
          f'        Average Test Results\n{test["results"].print_average_score()}')
    print(f'    Given a quote and a list of speakers, accuracy in predicting the true speaker:\n'
          f'        Training: {train["accuracy"]}\n'
          f'        Test:     {test["accuracy"]}\n')
    print(f'    Results in predicting the set of people cited in the article:\n'
          f'        Training:\n'
          f'            Precision: {train["precision"]}\n'
          f'            Recall:    {train["recall"]}\n'
          f'            F1:        {train["f1"]}\n'
          f'        Test:\n'
          f'            Precision: {test["precision"]}\n'
          f'            Recall:    {test["recall"]}\n'
          f'            F1:        {test["f1"]}\n')


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

            max_epochs = 200
            losses = ['log', 'hinge']
            log_penalties = ['l1', 'l2']
            alphas = [0.001, 0.01, 0.1]

            print('Evaluating quote detection...'.ljust(80), end='\r')
            print('\n  Baseline:')
            results = baseline_quote_detection(nlp)
            print(results.print_average_score())

            """
            for l in losses:
                for p in log_penalties:
                    print(f'\n  {p} {l}:')
                    accumulator = ResultAccumulator()
                    for alpha in alphas:
                        prefix = 'alpha={alpha}'
                        train_res, test_res = evaluate_quote_detection(l, p, alpha, max_epochs, nlp, cue_verbs, folds)
                        accumulator.add_results(train_res, test_res, f'alpha={alpha}')
                    train, test, name = accumulator.best_model()
                    print(f'    Best results with {name}'.ljust(80))
                    print(f'        Average Training Results\n{train.print_average_score()}\n'
                          f'        Average Test Results\n{test.print_average_score()}')
            """
            print('\n\nEvaluating quote attribution...')
            print('\n  Baseline:')
            acc, acc_lazy, p, r, p_lazy, r_lazy = baseline_quote_attribution(nlp, cue_verbs)
            print(f'    Given a quote and a list of speakers, accuracy in predicting the true speaker:\n'
                  f'        Baseline model:      {acc}\n'
                  f'        Lazy Baseline model: {acc_lazy}\n')
            print(f'    Results in predicting the set of people cited in the article:\n'
                  f'        Baseline model:\n'
                  f'            Precision: {p}\n'
                  f'            Recall:    {r}\n'
                  f'            F1:        {2 * p * r / (p + r)}\n'
                  f'        Lazy Baseline model:\n'
                  f'            Precision: {p_lazy}\n'
                  f'            Recall:    {r_lazy}\n'
                  f'            F1:        {2 * p_lazy * r_lazy / (p_lazy + r_lazy)}\n')

            best_ml_f1 = 0
            best_ml_parameters = ''
            best_ml_train = None
            best_ml_test = None

            for ovo in [True, False]:
                if ovo:
                    print('\n  One vs One')
                    extraction_methods = 3
                else:
                    print('\n  One vs All')
                    extraction_methods = 2
                for ext_method in list(range(1, extraction_methods + 1)):
                    for l, p in list(itertools.product(losses, log_penalties)):
                        print(f'    Results with {p}-{l} loss and feature extraction {ext_method}'.ljust(80))
                        best_train = None
                        best_test = None
                        best_f1 = 0
                        best_alpha = ''
                        for alpha in alphas:
                            train_res, test_res = evaluate_quote_attribution(l, p, alpha, ext_method, max_epochs, nlp,
                                                                             cue_verbs, folds, ovo)
                            if test_res['f1'] > best_f1:
                                best_f1 = test_res['f1']
                                best_alpha = alpha
                                best_train = train_res
                                best_test = test_res

                            if test_res['f1'] > best_ml_f1:
                                best_f1 = test_res['f1']
                                best_ml_parameters = f'{p}-{l} loss, feature extraction {ext_method}, alpha={alpha}'
                                best_ml_train = train_res
                                best_ml_test = test_res

                        print(f'    Best results with alpha={best_alpha}'.ljust(80))
                        pretty_print(best_train, best_test)

            print(f'\n\n    Best results from a machine learning model: {best_ml_parameters}')
            pretty_print(best_ml_train, best_ml_test)

        except IOError:
            raise CommandError('IO Error.')
