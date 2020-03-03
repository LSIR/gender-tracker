import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import KFold
from sklearn.preprocessing import PolynomialFeatures

from backend.db_management import load_labeled_articles
from backend.ml.quote_detection_dataset import QuoteDetectionDataset, detection_loader, subset, feature_extraction
from backend.ml.sgd import train, evaluate, cross_validate
from backend.ml.scoring import Results

# TODO: Make regularization term adjustable


def load_data(nlp, cue_verbs, poly):
    """
    Loads all labeled articles from the database and extracts feature vectors for them.

    :param nlp:
    :param cue_verbs:
    :param poly:
    :return:
    """
    train_articles, train_sentences, _, _ = load_labeled_articles(nlp)
    quote_detection_dataset = QuoteDetectionDataset(train_articles, train_sentences, cue_verbs, poly=poly)
    train_article_ids = np.array(list(map(lambda a: a.id, train_articles)))
    return train_article_ids, quote_detection_dataset


def predict_quotes(trained_model, sentences, cue_verbs, in_quotes, poly=None):
    """
    Computes probabilities that each sentence contains a quote.

    :param trained_model: sklearn.linear_model
        A trained model to predict probabilities for sentences.
    :param sentences: list(spaCy.doc)
        The list of all sentences to use for training, treated by a language model.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param in_quotes: list(list(int)).
        Whether each token in each sentence is between quotes or not.
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
    print(predictions)
    return predictions


def train_quote_detection(nlp, cue_verbs):
    poly = PolynomialFeatures(2, interaction_only=False)
    article_ids, quote_detection_dataset = load_data(nlp, cue_verbs, poly=poly)
    classifier = SGDClassifier(loss='log', alpha=0.1, penalty='l2')
    dataloader = detection_loader(quote_detection_dataset, train=True, batch_size=len(quote_detection_dataset))
    classifier, loss, accuracy = train(classifier, dataloader, 50)
    return classifier


def evaluate_unlabeled_sentences(trained_model, sentences, cue_verbs, in_quotes):
    """

    :param trained_model:
    :param sentences:
    :param cue_verbs:
    :param in_quotes:
    :return:
    """
    poly = PolynomialFeatures(2, interaction_only=False)
    return predict_quotes(trained_model, sentences, cue_verbs, in_quotes, poly=poly)


def evaluate_quote_detection(nlp, cue_verbs, cv_folds=5):
    poly = PolynomialFeatures(2, interaction_only=False)
    article_ids, quote_detection_dataset = load_data(nlp, cue_verbs, poly)

    for alpha in [0.001, 0.01, 0.1, 1]:
        print(f'\n  Regularization term: {alpha}')
        train_results, test_results = cross_validate(split_ids=article_ids,
                                                     dataset=quote_detection_dataset,
                                                     subset=subset,
                                                     dataloader=detection_loader,
                                                     alpha=alpha,
                                                     max_iter=200,
                                                     cv_folds=cv_folds)

        print('    Average Training Results')
        print(train_results.average_score())
        print('    Average Test Results')
        print(test_results.average_score())

    return quote_detection_dataset


