import numpy as np

from backend.ml.feature_extraction import extract_person_mentions, extract_speaker_features_ovo

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
    Finds the index of the mention that is the author of the quote. As there might be little differences in between what
    spaCy sees as Named Entities and what people see as Named Entities, we're just looking for an Named Entity that
    overlaps with the tag.

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
        # (m.end - 1) as m.end is the index of the first token after the span, and
        # reported_start is the first token of the reported author
        if m.start <= reported_end and (m.end - 1) >= reported_start:
            return index
    return -1


def create_input_matrix(articles, article_docs, sentence_ids, labels, cue_verbs):
    """
    Creates the input matrix from the raw data.

    :param articles: list(Article)
        A list of fully labeled articles
    :param article_docs: list(spacy.Doc)
        A list of of the docs for the fully labeled articles.
    :param sentence_ids: list(list(int))
        A list of sentences containing quotes that are in the training set, for each article in the articles list
    :param labels: list(list(list(int)))
        A list of authors (a list of token indices) for training sentences that contain quotes for each article
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return:
    """
    X = None
    y = None
    for i, article in enumerate(articles):
        article_doc = article_docs[i]
        people, mentions, full_names = extract_person_mentions(article_doc)
        for j, sent_index in enumerate(sentence_ids[i]):
            # List of indices of the tokens of the true author of the quote
            true_author = labels[i][j]
            true_mention_index = find_true_author_index(true_author, mentions)
            if true_mention_index >= 0:
                # Sample from the remaining mentions.
                neg_sample_index = np.random.randint(len(mentions) - 1)
                if neg_sample_index == true_mention_index:
                    neg_sample_index = len(mentions) - 1

                other_quotes = sentence_ids[i][:j] + sentence_ids[i][j + 1:]
                if np.random.random() > 0.5:
                    # Speaker 1 is the true speaker
                    speak_1 = mentions[true_mention_index]
                    speak_2 = mentions[neg_sample_index]
                    label = np.array([1])
                else:
                    # Speaker 2 is the true speaker
                    speak_1 = mentions[neg_sample_index]
                    speak_2 = mentions[true_mention_index]
                    label = np.array([0])

                features = extract_speaker_features_ovo(article, sent_index, other_quotes, speak_1, speak_2, cue_verbs)
                features = features.reshape(1, -1)
                if X is None:
                    X = features
                    y = label
                else:
                    X = np.concatenate((X, features), axis=0)
                    y = np.concatenate((y, label), axis=0)

            # else:
            # TODO: What to do when the author isn't a named entity? Just ignore it?

    return X, y


def evaluate_quote_attribution(articles, article_docs, sentence_ids, labels, cue_verbs, cv_folds=5):
    """
    Evaluates different classifiers, and returns their performance.

    Creates the input matrix from the raw data.

    :param articles: list(Article)
        A list of fully labeled articles
    :param article_docs: list(spacy.Doc)
        A list of of the docs for the fully labeled articles.
    :param sentence_ids: list(list(int))
        A list of sentences containing quotes that are in the training set, for each article in the articles list
    :param labels: list(list(list(int)))
        A list of authors (a list of token indices) for training sentences that contain quotes for each article
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param cv_folds: int
        The number of folds in cross-validation.
    :return:
    """
    X, y = create_input_matrix(articles, article_docs, sentence_ids, labels, cue_verbs)
    model_scores = {}
    for name, classifier in CLASSIFIERS.items():
        scoring = ['accuracy', 'precision_macro', 'f1_macro']
        # Returns scores for each split in a numpy array
        poly = PolynomialFeatures(2, interaction_only=True)
        poly.fit_transform(X)
        results = cross_validate(classifier, X, y, cv=cv_folds, scoring=scoring)
        # Change score for each split into average score
        results = {key: round(sum(val) / len(val), 3) for key, val in results.items()}
        model_scores[name] = results
    return model_scores
