from django.core.management.base import BaseCommand, CommandError
import spacy
import csv

from backend.db_management import load_sentence_labels, load_quote_authors
from backend.ml.quote_detection import evaluate_quote_detection
from backend.ml.quote_attribution_ovo import evaluate_ovo_quote_attribution, evaluate_ovo_speaker_prediction
from backend.ml.quote_attribution import evaluate_quote_attribution, evaluate_speaker_prediction


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
    help = 'Evaluates the different models using cross validation.'

    def handle(self, *args, **options):
        try:
            print('Loading language model...')
            nlp = spacy.load('fr_core_news_md')
            nlp.add_pipe(set_custom_boundaries, before="parser")

            print('Extracting labeled articles...')
            train_sentences, train_labels, train_in_quotes, _, _, _ = load_sentence_labels(nlp)
            print('Loading cue verbs...')
            with open('data/cue_verbs.csv', 'r') as f:
                reader = csv.reader(f)
                cue_verbs = set(list(reader)[0])

            print('Evaluating quote detection...')
            model_scores = evaluate_quote_detection(train_sentences, train_labels, cue_verbs, train_in_quotes)
            for name, score in model_scores.items():
                print(f'\n\n  Model: {name}\n'
                      f'    Accuracy:  {score["test_accuracy"]}\n'
                      f'    Precision: {score["test_precision_macro"]}\n'
                      f'    F1:        {score["test_f1_macro"]}\n')

            print('\nEvaluating quote attribution...')
            train_quotes, test_quotes = load_quote_authors()

            print('\n  One vs All scores:')
            model_scores = evaluate_quote_attribution(nlp, train_quotes, cue_verbs, cv_folds=2)
            for name, score in model_scores.items():
                print(f'\n\n  Model: {name}\n'
                      f'    Accuracy:  {score["test_accuracy"]}\n'
                      f'    Precision: {score["test_precision_macro"]}\n'
                      f'    F1:        {score["test_f1_macro"]}\n')

            print('\n  Correct Speaker Precision:')
            model_scores = evaluate_speaker_prediction(nlp, train_quotes, cue_verbs, cv_folds=2)
            for name, score in model_scores.items():
                print(f'\n\n    Model: {name}\n'
                      f'        Training Accuracy: {score["train_accuracy"]}\n'
                      f'        Test Accuracy:     {score["test_accuracy"]}\n')

            print('\n  One vs One scores:')
            model_scores = evaluate_ovo_quote_attribution(nlp, train_quotes, cue_verbs, cv_folds=2)
            for name, score in model_scores.items():
                print(f'\n\n  Model: {name}\n'
                      f'    Training:\n'
                      f'        Precision: {score["train_precision"]}\n'
                      f'        Recall:    {score["train_recall"]}\n'
                      f'        F1:        {score["train_f1"]}\n'
                      f'    Test:\n'
                      f'        Precision: {score["test_precision"]}\n'
                      f'        Recall:    {score["test_recall"]}\n'
                      f'        F1:        {score["test_f1"]}\n')

            print('\n  Correct Speaker Precision:')
            model_scores = evaluate_ovo_speaker_prediction(nlp, train_quotes, cue_verbs, cv_folds=2)
            for name, score in model_scores.items():
                print(f'\n\n    Model: {name}\n'
                      f'        Training Accuracy: {score["train_accuracy"]}\n'
                      f'        Test Accuracy:     {score["test_accuracy"]}\n')

        except IOError:
            raise CommandError('IO Error.')
