import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import KFold
from sklearn.preprocessing import PolynomialFeatures

from backend.db_management import load_labeled_articles
from backend.ml.helpers import print_scores
from backend.ml.quote_detection_dataset import QuoteDetectionDataset, detection_train_loader, \
    detection_test_loader, subset, feature_extraction
from backend.ml.sgd import train, evaluate


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
    article_ids, quote_detection_dataset = load_data(nlp, cue_verbs, poly=None)
    classifier = SGDClassifier(loss='log', alpha=0.1, penalty='l2')
    dataloader = detection_train_loader(quote_detection_dataset, batch_size=len(quote_detection_dataset))
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
    return predict_quotes(trained_model, sentences, cue_verbs, in_quotes, poly=None)


def evaluate_quote_detection(nlp, cue_verbs, cv_folds=5):
    poly = PolynomialFeatures(2, interaction_only=False)
    article_ids, quote_detection_dataset = load_data(nlp, cue_verbs, poly)
    print(f'Labeled article ids: {article_ids}')

    print(f'Evaluating Quote Detection')
    kf = KFold(n_splits=cv_folds)
    n_iter = 50
    folds = 0
    train_results = {
        'accuracy': [],
        'precision': [],
        'recall': [],
        'f1': [],
    }
    test_results = {
        'accuracy': [],
        'precision': [],
        'recall': [],
        'f1': [],
    }
    for train, test in kf.split(article_ids):
        # print(f'\n  Fold {folds}')
        folds += 1
        classifier = SGDClassifier(loss='log', alpha=0.1, penalty='l2')
        # print(f'\n  Splitting datasets into subsets')
        train_ids = article_ids[train]
        test_ids = article_ids[test]
        train_dataset = subset(quote_detection_dataset, train_ids)
        test_dataset = subset(quote_detection_dataset, test_ids)

        # print(f'    Training articles: {len(train_ids)}, ids: {train_ids}')
        # print(f'    Testing articles:  {len(test_ids)}, ids: {test_ids}')
        train_loader = detection_train_loader(train_dataset, batch_size=1)
        test_loader = detection_test_loader(test_dataset)
        for n in range(n_iter):
            for features, labels in train_loader:
                classifier.partial_fit(features, labels, classes=np.array([0, 1]))

        train_loader = detection_test_loader(train_dataset)
        train_scores = evaluate(classifier, train_loader)
        for key in train_results.keys():
            train_results[key].append(train_scores[key])
        test_scores = evaluate(classifier, test_loader)
        for key in test_results.keys():
            test_results[key].append(test_scores[key])

    train_averages = {}
    test_averages = {}
    for key in train_results.keys():
        if len(train_results[key]) > 0:
            train_averages[key] = sum(train_results[key]) / len(train_results[key])
        else:
            train_averages[key] = 'Na'
        if len(test_results[key]) > 0:
            test_averages[key] = sum(test_results[key]) / len(test_results[key])
        else:
            test_averages[key] = 'Na'

    print(print_scores('Average Training Results', train_averages))
    print(print_scores('Average Test Results', test_averages))

    return quote_detection_dataset


