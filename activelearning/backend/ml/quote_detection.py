import numpy as np
from backend.ml.feature_extraction import extract_quote_features, QUOTE_FEATURES
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import cross_validate
from sklearn.preprocessing import PolynomialFeatures


""" File containing all methods to build a model for quote detection. """


""" The model to use to classify """
CLASSIFIERS = {
    'L1 logistic': LogisticRegression(C=2, penalty='l1', solver='liblinear', max_iter=10000, multi_class='ovr'),
    'L2 logistic': LogisticRegression(C=2, penalty='l2', solver='liblinear', max_iter=10000, multi_class='ovr'),
    'Linear SVC': SVC(kernel='linear', C=2, probability=True, random_state=0),
}


def create_input_matrix(sentences, cue_verbs, in_quotes):
    """
    Creates the input matrix from the raw data.

    :param sentences: list(spaCy.doc)
        The list of all sentences to use for training, treated by a language model.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param in_quotes: list(list(int)).
        Whether each token in each sentence is between quotes or not
    :return: np.array
        The input matrix X, with shape: len(sentences) x QUOTE_FEATURES
    """
    X = np.zeros((len(sentences), QUOTE_FEATURES))
    for i, s in enumerate(sentences):
        feature_vector = extract_quote_features(s, cue_verbs, in_quotes[i])
        X[i, :] = feature_vector
    return X


def balance_classes(X, y):
    """
    Given the input matrices for an unbalanced classification task (where one class is present much more often than the
    other in the data), balances the classes so they both have the same number of samples by sub-sampling from the class
    that's more present.

    :param X: np.ndarray
        The input vectors.
    :param y: np.ndarray
        The labels.
    :return: np.ndarray, np.ndarray
        X, y: the input vectors and labels.
    """
    # Indices where the label is 0 (no reported speech is present)
    is_not_quote = (y == 0).nonzero()[0]
    # Indices where the label is 1 (reported speech is present)
    is_quote = (y == 1).nonzero()[0]
    # Takes random indices from the class most present, and all indices from the one least present
    if len(is_quote) < len(is_not_quote):
        subsample = np.random.choice(is_not_quote, size=len(is_quote), replace=False)
        indices = np.sort(np.concatenate((subsample, is_quote)))
    else:
        subsample = np.random.choice(is_quote, size=len(is_not_quote), replace=False)
        indices = np.sort(np.concatenate((subsample, is_not_quote)))
    # Only keeps some of the values
    sampled_y = np.take(y, indices)
    sampled_X = np.take(X, indices, axis=0)
    return sampled_X, sampled_y


def evaluate_quote_detection(sentences, labels, cue_verbs, in_quotes, cv_folds=5):
    """
    Evaluates different classifiers, and returns their performance.

    :param sentences: list(spaCy.doc)
        The list of all sentences to use for training, treated by a language model.
    :param labels: list(int)
        An int for each sentence: 1 if it was labeled as containing a quote, 0 if it wasn't.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param in_quotes: list(list(int)).
        Whether each token in each sentence is between quotes or not
    :param cv_folds: int
        The number of folds in cross-validation.
    :return:
    """
    X = create_input_matrix(sentences, cue_verbs, in_quotes)
    y = np.array(labels)
    X, y = balance_classes(X, y)
    poly = PolynomialFeatures(2, interaction_only=True)
    X = poly.fit_transform(X)
    model_scores = {}
    for name, classifier in CLASSIFIERS.items():
        scoring = ['accuracy', 'precision_macro', 'f1_macro']
        # Returns scores for each split in a numpy array
        results = cross_validate(classifier, X, y, cv=cv_folds, scoring=scoring)
        # Change score for each split into average score
        results = {key: round(sum(val) / len(val), 3) for key, val in results.items()}
        model_scores[name] = results
    return model_scores


def train_quote_detection(model, sentences, labels, cue_verbs, in_quotes):
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
    :param in_quotes: list(list(int)).
        Whether each token in each sentence is between quotes or not
    :return: sklearn.linear_model
        The trained model to predict probabilities for sentences.
    """
    X = create_input_matrix(sentences, cue_verbs, in_quotes)
    y = np.array(labels)
    X, y = balance_classes(X, y)
    poly = PolynomialFeatures(2, interaction_only=True)
    X = poly.fit_transform(X)
    classifier = CLASSIFIERS[model]
    classifier.fit(X, y)
    return classifier


def predict_quotes(trained_model, sentences, cue_verbs, in_quotes):
    """
    Computes probabilities that each sentence contains a quote.

    :param trained_model: sklearn.linear_model
        A trained model to predict probabilities for sentences.
    :param sentences: list(spaCy.doc)
        The list of all sentences to use for training, treated by a language model.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param in_quotes: list(list(int)).
        Whether each token in each sentence is between quotes or not
    :return: np.array()
        The probability for each sentence.
    """
    X = create_input_matrix(sentences, cue_verbs, in_quotes)
    poly = PolynomialFeatures(2, interaction_only=True)
    X = poly.fit_transform(X)
    return trained_model.predict_proba(X)[:, 1]
