import csv
import itertools

from django.core.management.base import BaseCommand, CommandError

from backend.ml.author_prediction import evaluate_author_prediction
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


def pretty_print_string(train, test):
    return f'    Average Training Results\n{train["results"].print_average_score()}\n' + \
           f'    Average Test Results\n{test["results"].print_average_score()}\n\n' + \
           f'    Given a quote and a list of speakers, accuracy in predicting the true speaker:\n' + \
           f'        Training: {train["accuracy"]}\n' + \
           f'        Test:     {test["accuracy"]}\n\n' + \
           f'    Results in predicting the set of people cited in the article:\n' + \
           f'        Training:\n' + \
           f'            Precision: {train["precision"]}\n' + \
           f'            Recall:    {train["recall"]}\n' + \
           f'            F1:        {train["f1"]}\n' + \
           f'        Test:\n' + \
           f'            Precision: {test["precision"]}\n' + \
           f'            Recall:    {test["recall"]}\n' + \
           f'            F1:        {test["f1"]}\n\n\n'


def pretty_print(train, test):
    print(pretty_print_string(train, test))


class Command(BaseCommand):
    help = 'Evaluates the different models using cross validation.'

    def add_arguments(self, parser):
        parser.add_argument('--folds', type=int, help='The number of folds to perform cross-validation on. Default: 5')
        parser.add_argument('--epochs', type=int, help='The maximum number of epochs to train for. Default: 500')
        parser.add_argument('--loss', help='The loss to use. Default: all are evaluated.',
                            choices=['log', 'hinge', 'all'])
        parser.add_argument('--penalty', help='The penalty to use. Default: all are evaluated.',
                            choices=['l1', 'l2', 'all'], )
        parser.add_argument('--exp', help='The degree of feature expansion for author prediction and quote detection.',
                            type=int, default=2)

    def handle(self, *args, **options):
        folds = 5
        if options['folds']:
            folds = options['folds']

        max_epochs = 500
        if options['epochs']:
            max_epochs = options['epochs']

        losses = ['log', 'hinge']
        if options['loss']:
            if options['loss'] == 'log':
                losses = ['log']
            elif options['loss'] == 'hinge':
                losses = ['hinge']

        log_penalties = ['l1', 'l2']
        if options['penalty']:
            if options['penalty'] == 'l1':
                log_penalties = ['l1']
            elif options['penalty'] == 'l2':
                log_penalties = ['l2']

        try:
            with open('logs.txt', 'w') as f:
                f.write(f'Evaluation:\n'
                        f'  {folds}-fold cross validation\n'
                        f'  max epochs: {max_epochs}\n\n')

            print('\nLoading language model...'.ljust(80), end='\r')
            nlp = load_nlp()

            print('Loading cue verbs...'.ljust(80), end='\r')
            with open('data/cue_verbs.csv', 'r') as f:
                reader = csv.reader(f)
                cue_verbs = set(list(reader)[0])

            alphas = [0.01, 0.1]

            print('Evaluating quote detection...'.ljust(80))
            print('\n  Baseline:')
            results = baseline_quote_detection(nlp)
            print(results.print_average_score())
            with open('logs.txt', 'a') as f:
                f.write(f'  Baseline quote detection:\n{results.print_average_score()}\n')

            for l in losses:
                for p in log_penalties:
                    print(f'  {p} {l}:')
                    accumulator = ResultAccumulator()
                    for alpha in alphas:
                        train_res, test_res = evaluate_quote_detection(l, p, alpha, max_epochs, nlp, cue_verbs, folds)
                        with open('logs.txt', 'a') as f:
                            f.write(f'  Quote detection: {p}-{l} loss, alpha={alpha}\n'
                                    f'    Training results:\n{train_res.print_average_score()}\n'
                                    f'    Test results:\n{test_res.print_average_score()}\n')
                        accumulator.add_results(train_res, test_res, f'alpha={alpha}')
                    train, test, name = accumulator.best_model()
                    print(f'      Best results with {name}'.ljust(80))
                    print(f'        Average Training Results\n{train.print_average_score()}\n'
                          f'        Average Test Results\n{test.print_average_score()}\n\n')

            print('\n\nEvaluating speaker prediction...')
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
                  f'            F1:        {2 * p_lazy * r_lazy / (p_lazy + r_lazy)}\n\n')

            print('Speaker prediction: classifying each named entity in a text as either the author of a quote or not'
                  ', but not assigning a single named entity to each quote.')
            for l in losses:
                for p in log_penalties:
                    print(f'   Speaker Prediction Results with {p}-{l} loss'.ljust(80))
                    best_train_res = None
                    best_test_res = None
                    best_train_set = None
                    best_test_set = None
                    best_f1 = 0
                    best_alpha = ''
                    for alpha in alphas:
                        exp_degree = options['exp']
                        train_res, test_res, train_set, test_set = evaluate_author_prediction(l, p, alpha, max_epochs,
                                                                                              nlp, cue_verbs,
                                                                                              exp_degree, folds)

                        acc, pre, rec, f1 = test_set.average_score()
                        if f1 > best_f1:
                            best_f1 = f1
                            best_alpha = alpha
                            best_train_res = train_res
                            best_test_res = test_res
                            best_train_set = train_set
                            best_test_set = test_set

                    print(f'      Best results with alpha={best_alpha}'.ljust(80))
                    print(f'      Performance in predicting each named entity'.ljust(80))
                    print(f'        Average Training Results\n{best_train_res.print_average_score()}\n'
                          f'        Average Test Results\n{best_test_res.print_average_score()}\n\n')
                    print(f'      Performance in predicting each author name'.ljust(80))
                    print(f'        Average Training Results\n{best_train_set.print_average_score()}\n'
                          f'        Average Test Results\n{best_test_set.print_average_score()}\n\n')

            print('\n\nEvaluating quote attribution...')

            best_ml_f1 = 0
            best_ml_parameters = ''
            best_ml_train = None
            best_ml_test = None

            # TODO: Also train OVO (for now it's super slow though)
            for ovo in [False]:
                if ovo:
                    print('\n  One vs One')
                    extraction_methods = 3
                else:
                    print('\n  One vs All')
                    extraction_methods = 4
                for ext_method in list(range(2, extraction_methods + 1)):
                    for l, p in list(itertools.product(losses, log_penalties)):
                        print(f'   Results with {p}-{l} loss and feature extraction {ext_method}'.ljust(80))
                        best_train = None
                        best_test = None
                        best_f1 = 0
                        best_alpha = ''
                        for alpha in alphas:
                            train_res, test_res = evaluate_quote_attribution(l, p, alpha, ext_method, max_epochs, nlp,
                                                                             cue_verbs, folds, ovo)

                            with open('logs.txt', 'a') as f:
                                f.write(f'  Quote attribution: one vs one: {ovo}, {ext_method}-feature extraction,'
                                        f' {p}-{l} loss, alpha={alpha}\n'
                                        f'{pretty_print_string(train_res, test_res)}\n')

                            if test_res['f1'] > best_f1:
                                best_f1 = test_res['f1']
                                best_alpha = alpha
                                best_train = train_res
                                best_test = test_res

                            if test_res['f1'] > best_ml_f1:
                                best_ml_f1 = test_res['f1']
                                best_ml_parameters = f'{p}-{l} loss, feature extraction {ext_method}, alpha={alpha}'
                                best_ml_train = train_res
                                best_ml_test = test_res

                        print(f'    Best results with alpha={best_alpha}'.ljust(80))
                        print(pretty_print_string(best_train, best_test))
                        print('\n\n')

            print(f'\n\n    Best results from a machine learning model: {best_ml_parameters}')
            print(pretty_print_string(best_ml_train, best_ml_test))

            with open('logs.txt', 'a') as f:
                f.write(f'  Best results for quote attribution: {best_ml_parameters}\n'
                        f'{pretty_print_string(best_ml_train, best_ml_test)}')

        except IOError:
            raise CommandError('IO Error.')
