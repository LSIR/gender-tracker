from django.core.management.base import BaseCommand, CommandError
import spacy
import csv

from backend.db_management import load_sentence_labels, load_quote_authors
from backend.ml.quote_detection import evaluate_quote_detection
from backend.ml.quote_attribution import evaluate_quote_attribution


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
            with open('../data/cue_verbs.csv', 'r') as f:
                reader = csv.reader(f)
                cue_verbs = set(list(reader)[0])

            print('Evaluating quote detection...')
            model_scores = evaluate_quote_detection(train_sentences, train_labels, cue_verbs, train_in_quotes)
            for name, score in model_scores.items():
                print(f'\n\nModel: {name}\n'
                      f'\tAccuracy:  {score["test_accuracy"]}\n'
                      f'\tPrecision: {score["test_precision_macro"]}\n'
                      f'\tF1:        {score["test_f1_macro"]}\n')

            print('\nEvaluating quote attribution...')
            articles, article_docs, train_ids, train_labels, test_ids, test_labels = load_quote_authors(nlp)
            model_scores = evaluate_quote_attribution(articles, article_docs, train_ids, train_labels, cue_verbs)
            for name, score in model_scores.items():
                print(f'\n\nModel: {name}\n'
                      f'\tAccuracy:  {score["test_accuracy"]}\n'
                      f'\tPrecision: {score["test_precision_macro"]}\n'
                      f'\tF1:        {score["test_f1_macro"]}\n')

        except IOError:
            raise CommandError('IO Error.')
