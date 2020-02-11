import numpy as np
from backend.ml.feature_extraction import extract_quote_features, QUOTE_FEATURES
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import cross_validate


""" File containing all methods to build a model for quote detection. """


""" The model to use to classify """
CLASSIFIERS = {
    'L1 logistic': LogisticRegression(C=2, penalty='l1', solver='liblinear', max_iter=10000),
    'L2 logistic': LogisticRegression(C=2, penalty='l2', solver='liblinear', max_iter=10000),
    'Linear SVC': SVC(kernel='linear', C=2, probability=True, random_state=0),
}


def create_input_matrix(sentences, cue_verbs):
    """
     Trains the model.

    :param sentences: list(spaCy.doc)
        The list of all sentences to use for training, treated by a language model.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return: np.array
        The input matrix X, with shape: len(sentences) x QUOTE_FEATURES
    """
    X = np.zeros((len(sentences), QUOTE_FEATURES))
    for i, s in enumerate(sentences):
        feature_vector = extract_quote_features(s, cue_verbs)
        X[i, :] = feature_vector
    return X


def evaluate_classifiers(sentences, labels, cue_verbs):
    """
    Evaluates different classifiers, and returns their performance.

    :param sentences: list(spaCy.doc)
        The list of all sentences to use for training, treated by a language model.
    :param labels: list(int)
        An int for each sentence: 1 if it was labeled as containing a quote, 0 if it wasn't.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return:
    """
    X = create_input_matrix(sentences, cue_verbs)
    y = np.array(labels)
    model_scores = {}
    for name, classifier in CLASSIFIERS.items():
        scoring = ['accuracy', 'precision_macro', 'f1_macro']
        model_scores[name] = cross_validate(classifier, X, y, cv=2, scoring=scoring)
    return model_scores


def train(model, sentences, labels, cue_verbs):
    """
    Trains a classifier to detect if sentences contains quotes or not.

    :param model: string
        The model to use for classification. One of {'L1 logistic', 'L2 logistic', 'Linear SVC'}.
    :param sentences: list(spaCy.doc)
        The list of all sentences to use for training, treated by a language model.
    :param labels: list(int)
        An int for each sentence: 1 if it was labeled as containing a quote, 0 if it wasn't.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return: sklearn.linear_model
        The trained model to predict probabilities for sentences.
    """
    X = create_input_matrix(sentences, cue_verbs)
    y = np.array(labels)
    classifier = CLASSIFIERS[model]
    classifier.fit(X, y)
    return classifier


def predict_quotes(trained_model, sentences, cue_verbs):
    """
    Computes probabilities that each sentence contains a quote.

    :param trained_model: sklearn.linear_model
        A trained model to predict probabilities for sentences.
    :param sentences: list(spaCy.doc)
        The list of all sentences to use for training, treated by a language model.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return: np.array()
        The probability for each sentence.
    """
    X = create_input_matrix(sentences, cue_verbs)
    return trained_model.predict_proba(X)
