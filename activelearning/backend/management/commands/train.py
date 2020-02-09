import spacy

from django.core.management.base import BaseCommand, CommandError

from backend.models import Article, UserLabel
from backend.helpers import aggregate_label
from backend.ml.quote_detection import train


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
            articles = Article.objects.filter(labeled__fully_labeled=1)
            all_sentences = []
            all_labels = []
            for article in articles:
                start = 0
                for sentence_index, end in enumerate(article.sentences['sentences']):
                    tokens = article.tokens['tokens'][start:end]
                    all_sentences.append(form_sentence(nlp, tokens))
                    sentence_labels, _, _ = aggregate_label(article, sentence_index)
                    all_labels.append(sum(sentence_labels))
                    start = end + 1
            print('Training model...')
            # Replace with actual cue verbs
            cue_verbs = ['dire']
            train(model, all_sentences, all_labels, cue_verbs)
            print('Done')

        except IOError:
            raise CommandError('IO Error.')
