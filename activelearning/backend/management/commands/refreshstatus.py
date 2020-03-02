from django.core.management.base import BaseCommand

from backend.models import Article, UserLabel
from backend.helpers import label_consensus
from backend.db_management import CONSENSUS_THRESHOLD, COUNT_THRESHOLD


class Command(BaseCommand):
    help = 'Goes over all articles and user labels, and recomputes if each sentence is labeled or not. This should ' \
           'not change anything in the tables unless the requirements for a sentence to be labeled have changed.'

    def handle(self, *args, **options):

        articles = Article.objects.all()
        for a in articles:
            labeled = []
            for s_index in range(len(a.sentences['sentences'])):
                userlabels = UserLabel.objects.filter(article=a, sentence_index=s_index).exclude(labels__labels=[])

                admin_labels = userlabels.filter(admin_label=True)

                if len(admin_labels) > 0:
                    labeled.append(1)
                else:
                    labels = [userlabel.labels['labels'] for userlabel in userlabels]
                    authors = [userlabel.author_index['author_index'] for userlabel in userlabels]
                    label, author, consensus = label_consensus(labels, authors)

                    is_labeled = int(consensus >= CONSENSUS_THRESHOLD and len(labels) >= COUNT_THRESHOLD)
                    labeled.append(is_labeled)

            predictions = len(a.sentences['sentences']) * [0]
            a.confidence['predictions'] = predictions
            fully_labeled = int(sum(labeled) == len(a.sentences['sentences']))
            a.labeled = {
                'labeled': labeled,
                'fully_labeled': fully_labeled,
            }
            a.save()
