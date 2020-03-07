import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import PolynomialFeatures

from backend.db_management import load_labeled_articles
from backend.ml.quote_detection_dataset import QuoteDetectionDataset, detection_loader, subset
from backend.ml.quote_detection_feature_extraction import feature_extraction
from backend.ml.sgd import train, cross_validate


def load_data(nlp, cue_verbs, poly):
    """
    Loads all labeled articles from the database and extracts feature vectors for them.

    :param nlp: spaCy.Language
        The language model used to tokenize the text.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param poly: sklearn.preprocessing.PolynomialFeatures
        If defined, used to perform feature extraction.
    :return: list(int), QuoteDetectionDataset
        The ids of all articles in the dataset, and the dataset.
    """
    train_articles, train_sentences, _, _ = load_labeled_articles(nlp)
    quote_detection_dataset = QuoteDetectionDataset(train_articles, train_sentences, cue_verbs, poly=poly)
    train_article_ids = np.array(list(map(lambda a: a.id, train_articles)))
    return train_article_ids, quote_detection_dataset


def predict_quotes(trained_model, sentences, cue_verbs, in_quotes, poly=None):
    """
    Computes probabilities that each sentence contains a quote.

    :param trained_model: sklearn.linear_model.SGDClassifier
        A trained model to predict probabilities for sentences.
    :param sentences: list(spaCy.doc)
        The list of all sentences to evaluate, treated by a language model.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param in_quotes: list(list(int)).
        Whether each token in each sentence is between quotes or not.
    :param poly: sklearn.preprocessing.PolynomialFeatures
        If defined, used to perform feature extraction.
    :return: np.array()
        The probability for each sentence.
    """
    features = []
    for i, sentence in enumerate(sentences):
        sentence_features = feature_extraction(sentence, cue_verbs, in_quotes[i])
        if poly:
            sentence_features = poly.fit_transform(sentence_features.reshape((-1, 1))).reshape((-1,))
        features.append(sentence_features)
    X = np.array(features)
    predictions = trained_model.predict_proba(X)[:, 1]
    return predictions


def train_quote_detection(nlp, cue_verbs):
    """
    Trains a classifier to perform quote detection, on all fully labeled articles in the training set.

    :param nlp: spaCy.Language
        The language model used to tokenize the text.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return: sklearn.linear_model.SGDClassifier
        The trained classifier
    """
    poly = PolynomialFeatures(2, interaction_only=False)
    article_ids, quote_detection_dataset = load_data(nlp, cue_verbs, poly=poly)
    classifier = SGDClassifier(loss='log', alpha=0.1, penalty='l2')
    dataloader = detection_loader(quote_detection_dataset, train=True, batch_size=10)
    eval_dataloader = detection_loader(quote_detection_dataset, train=False, batch_size=len(quote_detection_dataset))
    classifier, accuracy = train(classifier, dataloader, eval_dataloader, 1000)
    return classifier


def evaluate_unlabeled_sentences(trained_model, sentences, cue_verbs, in_quotes):
    """
    Uses a trained quote detection model to predict whether new sentences are also quotes.

    :param trained_model: sklearn.linear_model.SGDClassifier
        A trained model to predict probabilities for sentences.
    :param sentences: list(spaCy.doc)
        The list of all sentences to to predict.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param in_quotes: list(list(int)).
        Whether each token in each sentence is between quotes or not.
    :return: np.array()
        The probability that each sentence contains a quote.
    """
    poly = PolynomialFeatures(2, interaction_only=False)
    return predict_quotes(trained_model, sentences, cue_verbs, in_quotes, poly=poly)


def evaluate_quote_detection(loss, penalty, alpha, max_iter, nlp, cue_verbs, cv_folds=5, prefix=''):
    """
    Trains different models for quote detection.

    :param loss: string
        One of {'log', 'hinge'}. The loss function to use.
    :param penalty: string
        One of {'l1', 'l2}. The penalty to use for training
    :param alpha: float
        The regularization to use for training
    :param max_iter: int
        The maximum number of epochs to train for
    :param nlp: spaCy.Language
        The language model used to tokenize the text.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param cv_folds: int
        The number of cross-validation folds to perform for each model.
    :return: QuoteDetectionDataset
        The dataset that was used for quote detection.
    """
    poly = PolynomialFeatures(2, interaction_only=False)
    article_ids, quote_detection_dataset = load_data(nlp, cue_verbs, poly)

    train_results, test_results = cross_validate(loss=loss,
                                                 penalty=penalty,
                                                 split_ids=article_ids,
                                                 dataset=quote_detection_dataset,
                                                 subset=subset,
                                                 dataloader=detection_loader,
                                                 alpha=alpha,
                                                 max_iter=max_iter,
                                                 cv_folds=cv_folds,
                                                 prefix=prefix)

    return train_results, test_results


