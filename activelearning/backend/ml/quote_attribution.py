import numpy as np
from backend.ml.feature_extraction import extract_person_mentions, extract_speaker_features, SPEAKER_FEATURES
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import cross_validate
from sklearn.preprocessing import PolynomialFeatures
from functools import reduce


""" File containing all methods to build a model for quote attribution. """


""" The models used for quote attribution """
CLASSIFIERS = {
    'L1 logistic': LogisticRegression(C=2, penalty='l1', solver='liblinear', max_iter=10000, multi_class='ovr'),
    'L2 logistic': LogisticRegression(C=2, penalty='l2', solver='liblinear', max_iter=10000, multi_class='ovr'),
    'Linear SVC': SVC(kernel='linear', C=2, probability=True, random_state=0),
}


def find_true_author_index(true_author, mentions):
    """
    Finds the index of the mention that is the author of the quote.

    :param true_author: list(int)
        The index of the tokens of the true_author.
    :param mentions: list(spaCy.Span)
        The mentions of PER named entites in the article.
    :return: int
        The index of the mention in the list of mentions.
    """
    reported_start = true_author[0]
    reported_end = true_author[-1]
    for index, m in enumerate(mentions):
        # (m.end - 1) as m.end is the index of the first token after the span, and reported_start is the first token
        # of the reported author
        if m.start <= reported_end and (m.end - 1) >= reported_start:
            return index
    return -1


def create_input_matrix(articles, sentence_ids, labels, cue_verbs):
    """
    Creates the input matrix from the raw data.

    :param articles: list(Article)
        A list of fully labeled articles
    :param sentence_ids: list(list(int))
        A list of sentences containing quotes that are in the training set, for each article in the articles list
    :param labels: list(list(list(int)))
        A list of authors (a list of token indices) for training sentences that contain quotes for each article
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return:
    """
    X = None
    for i, article in enumerate(articles):
        people, mentions, full_names = extract_person_mentions(article)
        for j, sent_index in enumerate(sentence_ids[i]):
            # List of indices of the tokens of the true author of the quote
            true_author = labels[i, j]
            true_mention = find_true_author_index(true_author, mentions)
            if true_mention >= 0:
                # TODO: Extract negative sample
                print('Create Labels')
            else:
                # TODO: What to do when the author isn't a named entity? Just ignore it?
                print('WHAT TO DO HERE')
    return X
