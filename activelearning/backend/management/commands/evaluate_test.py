import csv
import itertools

from django.core.management.base import BaseCommand, CommandError

from backend.ml.author_prediction import evaluate_author_prediction_test
from backend.ml.baseline import baseline_quote_detection, baseline_quote_attribution
from backend.ml.quote_attribution import evaluate_quote_attribution
from backend.ml.quote_detection import evaluate_quote_detection
from backend.ml.scoring import ResultAccumulator
from backend.xml_parsing.helpers import load_nlp


class Command(BaseCommand):
    help = 'Evaluates the different models using cross validation.'

    def add_arguments(self, parser):
        parser.add_argument('--epochs', help='The maximum number of epochs to train for. Default: 500',
                            type=int, default=500)
        parser.add_argument('--alpha', help='The regularization to use. Default: 0.1', type=float, default=0.01)
        parser.add_argument('--loss', help='The loss to use. Default: log.', choices=['log', 'hinge'], default='log')
        parser.add_argument('--penalty', help='The penalty to use. Default: l2.', choices=['l1', 'l2'],  default='l2')
        parser.add_argument('--exp', help='The degree of feature expansion for author prediction and quote detection.',
                            type=int, default=2)

    def handle(self, *args, **options):

        try:
            print('\nLoading language model...'.ljust(80), end='\r')
            nlp = load_nlp()

            print('Loading cue verbs...'.ljust(80), end='\r')
            with open('data/cue_verbs.csv', 'r') as f:
                reader = csv.reader(f)
                cue_verbs = set(list(reader)[0])

            train_acc, train_acc_lazy, train_p, train_r, train_p_lazy, train_r_lazy =\
                baseline_quote_attribution(nlp, cue_verbs, test=False)
            test_acc, test_acc_lazy, test_p, test_r, test_p_lazy, test_r_lazy = \
                baseline_quote_attribution(nlp, cue_verbs, test=True)

            print('Author Predictions'.ljust(80))
            print('\n  Baseline:')
            print(f'     Training Set Performance')
            print(f'        Accuracy of predicting true Speaker')
            print(f'            {train_acc}')
            print(f'        Results in predicting the set of people cited in the article:\n'
                  f'            Precision: {train_p}\n'
                  f'            Recall:    {train_r}\n'
                  f'            F1:        {2 * train_p * train_r / (train_p + train_r)}\n')
            print(f'     Test Set Performance')
            print(f'        Accuracy of predicting true Speaker')
            print(f'            {test_acc}')
            print(f'        Results in predicting the set of people cited in the article:\n'
                  f'            Precision: {test_p}\n'
                  f'            Recall:    {test_r}\n'
                  f'            F1:        {2 * test_p * test_r / (test_p + test_r)}\n')

            print('\n  Lazy Baseline:')
            print(f'     Training Set Performance')
            print(f'        Accuracy of predicting true Speaker')
            print(f'            {train_acc_lazy}')
            print(f'        Results in predicting the set of people cited in the article:\n'
                  f'            Precision: {train_p_lazy}\n'
                  f'            Recall:    {train_r_lazy}\n'
                  f'            F1:        {2 * train_p_lazy * train_r_lazy / (train_p_lazy + train_r_lazy)}\n')
            print(f'     Test Set Performance')
            print(f'        Accuracy of predicting true Speaker')
            print(f'            {test_acc_lazy}')
            print(f'        Results in predicting the set of people cited in the article:\n'
                  f'            Precision: {test_p_lazy}\n'
                  f'            Recall:    {test_r_lazy}\n'
                  f'            F1:        {2 * test_p_lazy * test_r_lazy / (test_p_lazy + test_r_lazy)}\n')

            print('  ML Author Prediction')
            epochs = options['epochs']
            alpha = options['exp']
            loss = options['loss']
            penalty = options['penalty']
            exp_degree = options['exp']
            _, train_res, test_res, train_authors, test_authors, test_lists =\
                evaluate_author_prediction_test(loss, penalty, alpha, epochs, nlp, cue_verbs, exp_degree)

            print(f'    Training Set Performance')
            print(f'        Binary Classification for NEs\n{train_res.print_average_score()}\n')
            print(f'        Predicting the people cited in an article\n{train_authors.print_average_score()}\n')
            print(f'    Test Set Performance')
            print(f'        Binary Classification for NEs\n{test_res.print_average_score()}\n')
            print(f'        Predicting the people cited in an article\n{test_authors.print_average_score()}\n')
            print(f'        Article by article performance:')
            for i, results in enumerate(test_lists):
                print(f'          Article {i}')
                print(f'            All names: {results["all"]}')
                print(f'            Cited:     {results["cited"]}')
                print(f'            Predicted: {results["predicted"]}')

        except IOError:
            raise CommandError('IO Error.')