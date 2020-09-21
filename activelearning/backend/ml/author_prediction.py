import numpy as np
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import KFold
from sklearn.preprocessing import PolynomialFeatures

from backend.ml.helpers import extract_speaker_names
from backend.db_management import load_quote_authors
from backend.ml.author_prediction_dataset import AuthorPredictionDataset, subset, author_prediction_loader
from backend.ml.scoring import Results
from backend.ml.sgd import train, evaluate

"""
File with the second way of extracting authors for quotes. Instead of trying to determine which Named Entity is the
author of a quote, we try to predict whether each named entity authored a quote. This allows us to train a simple
binary classifier.
"""


def load_data(nlp, cue_verbs, poly):
    """
    Loads the datasets to perform article quotee extraction.

    :param nlp: spaCy.Language
        The language model used to tokenize the text.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param poly: sklearn.preprocessing.PolynomialFeatures
        If defined, used to perform feature extraction.
    :return: np.array(dict), np.array(int), QuoteAttributionDataset
        * Array of dicts containing training and test quotes, respectively. Keys:
            * 'article': models.Article, the article containing the quote
            * 'sentences': list(spaCy.Doc), the spaCy.Doc for each sentence in the article.
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author of the quote.
        * The dataset
    """
    train_dicts, _ = load_quote_authors(nlp)
    author_prediction_dataset = AuthorPredictionDataset(train_dicts, cue_verbs, poly)
    return np.array(train_dicts), author_prediction_dataset


def predict_authors(trained_model, dataset, article):
    """
    Predicts if each speaker in the article is the author of a quote.

    :param trained_model: SGDClassifier
        The classifier to use to predict the author of the quote.
    :param dataset: AuthorPredictionDataset
        The dataset containing the article for which we want to predict the author of a quote.
    :param article: models.Article
        The article for which we want to predict the speaker of each quote.
    :return: Optional(np.array(int), np.array(int))
        The true and predicted author indices, or None if no speakers were found in the article.
    """
    start_index, end_index, _ = dataset.get_article_features(article.id)
    if start_index < end_index:
        people_names_in_article = article.people['people']

        speaker_features, speaker_labels = dataset[start_index:end_index]
        predicted_labels = trained_model.predict(np.array(speaker_features))

        true_names = extract_speaker_names(article, speaker_labels)
        predicted_names = extract_speaker_names(article, predicted_labels)

        true_labels = []
        predicted_labels = []

        for name in people_names_in_article:
            true_labels.append(int(name in true_names))
            predicted_labels.append(int(name in predicted_names))

        return true_labels, predicted_labels


def evaluate_author_prediction(loss, penalty, alpha, max_iter, nlp, cue_verbs, poly_degree, cv_folds=5):
    """
    Evaluates the author prediction model using cross-validation, only on the articles in the training set, on the
    following metrics:
        * Accuracy in speaker prediction: given a named entity, the model tries to predict if that named entity is the
          quotee for any quote.
        * Speaker extraction: Given an article, find all people that are quoted in the article.

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
    :param poly_degree: int
        The degree to which polynomial feature expansion should be performed
    :param cv_folds: int
        The number of cross-validation folds to perform.
    :return: Scoring.Results, Scoring.Results, Scoring.Results, Scoring.Results
        The results of cross-validation
            * CV training results of predicting if each named entity is the quotee for a sentence or not
            * CV test results of predicting if each named entity is the quotee for a sentence or not
            * CV training results of predicting if each person (across all mentions of that person) is cited in the
              article or not
            * CV test results of predicting if each person (across all mentions of that person) is cited in the article
              or not
    """
    poly = PolynomialFeatures(poly_degree, interaction_only=True, include_bias=True)
    article_dicts, author_prediction_dataset = load_data(nlp, cue_verbs, poly)

    kf = KFold(n_splits=cv_folds)

    train_results = Results()
    test_results = Results()

    train_author_set_results = Results()
    test_author_set_results = Results()

    n = 0
    for train_indices, test_indices in kf.split(article_dicts):
        prefix = f'      Evaluating with alpha={alpha}: {int(100 * n / cv_folds)}% {10 * n // cv_folds * "█"}'.ljust(50)
        n += 1

        classifier = SGDClassifier(loss=loss, alpha=alpha, penalty=penalty, warm_start=True)

        train_articles = article_dicts[train_indices]
        train_ids = list(map(lambda a: a['article'].id, train_articles))

        test_articles = article_dicts[test_indices]
        test_ids = list(map(lambda a: a['article'].id, test_articles))

        train_dataset = subset(author_prediction_dataset, train_ids)
        test_dataset = subset(author_prediction_dataset, test_ids)

        train_loader = author_prediction_loader(train_dataset, train=True, batch_size=10)
        test_loader = author_prediction_loader(test_dataset, train=False, batch_size=len(test_dataset))

        classifier, _ = train(classifier, train_loader, test_loader, max_iter, print_prefix=prefix)

        train_loader = author_prediction_loader(train_dataset, train=False, batch_size=len(train_dataset))
        train_results.add_scores(evaluate(classifier, train_loader))
        test_results.add_scores(evaluate(classifier, test_loader))

        train_people_cited_true_labels = []
        train_people_cited_predicted_labels = []

        for article in train_articles:
            prediction_results = predict_authors(classifier, author_prediction_dataset, article['article'])
            if prediction_results:
                true_labels, predicted_labels = prediction_results
                train_people_cited_true_labels += true_labels
                train_people_cited_predicted_labels += predicted_labels

        train_labels = zip(train_people_cited_true_labels, train_people_cited_predicted_labels)
        accuracy = sum([true == predicted for true, predicted in train_labels]) / len(train_people_cited_true_labels)
        precision, recall, f1, _ = precision_recall_fscore_support(train_people_cited_true_labels,
                                                                   train_people_cited_predicted_labels,
                                                                   zero_division=0,
                                                                   average='binary')
        train_people_cited_scores = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
        }
        train_author_set_results.add_scores(train_people_cited_scores)

        test_people_cited_true_labels = []
        test_people_cited_predicted_labels = []

        for article in test_articles:
            prediction_results = predict_authors(classifier, author_prediction_dataset, article['article'])
            if prediction_results:
                true_labels, predicted_labels = prediction_results
                test_people_cited_true_labels += true_labels
                test_people_cited_predicted_labels += predicted_labels

        test_labels = zip(test_people_cited_true_labels, test_people_cited_predicted_labels)
        accuracy = sum([true == predicted for true, predicted in test_labels]) / len(test_people_cited_true_labels)
        precision, recall, f1, _ = precision_recall_fscore_support(test_people_cited_true_labels,
                                                                   test_people_cited_predicted_labels,
                                                                   zero_division=0,
                                                                   average='binary')
        test_people_cited_scores = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
        }
        test_author_set_results.add_scores(test_people_cited_scores)

    return train_results, test_results, train_author_set_results, test_author_set_results


def evaluate_author_prediction_test(loss, penalty, alpha, max_iter, nlp, cue_verbs, poly_degree):
    """
    Trains an author prediction model on the whole training set, and evaluates it on the test set. Computes:
        * Accuracy in speaker prediction: given a named entity, the model tries to predict if that named entity is the
          quotee for any quote.
        * Speaker extraction: Given an article, find all people that are quoted in the article.

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
    :param poly_degree: int
        The degree to which polynomial feature expansion should be performed
    :return: Scoring.Results, Scoring.Results, Scoring.Results, Scoring.Results, list[dict]
        The results of cross-validation
            * CV training results of predicting if each named entity is the quotee for a sentence or not
            * CV test results of predicting if each named entity is the quotee for a sentence or not
            * CV training results of predicting if each person (across all mentions of that person) is cited in the
              article or not
            * For each article in the test set, has a dictionary containing the keys:
                * 'all': all of the names of people found in the article
                * 'cited': the names of people cited in the article
                * 'predicted': the names of people predicted to have been cited in the article
    """
    # Load Data
    poly = PolynomialFeatures(poly_degree, interaction_only=True, include_bias=True)
    train_dicts, test_dicts = load_quote_authors(nlp)
    train_dataset = AuthorPredictionDataset(train_dicts, cue_verbs, poly)
    train_loader = author_prediction_loader(train_dataset, train=True, batch_size=10)
    test_dataset = AuthorPredictionDataset(test_dicts, cue_verbs, poly)
    test_loader = author_prediction_loader(test_dataset, train=False, batch_size=len(test_dataset))

    # Train Model
    train_results = Results()
    train_author_set_results = Results()
    classifier = SGDClassifier(loss=loss, alpha=alpha, penalty=penalty, warm_start=True)
    prefix = f'      Training Author Prediction Model'.ljust(50)
    classifier, _ = train(classifier, train_loader, test_loader, max_iter, print_prefix=prefix)
    train_loader = author_prediction_loader(train_dataset, train=False, batch_size=len(train_dataset))
    train_results.add_scores(evaluate(classifier, train_loader))

    # Evaluate Model
    test_results = Results()
    test_author_set_results = Results()
    test_results.add_scores(evaluate(classifier, test_loader))

    # Evaluate the precision in extracting speakers
    train_people_cited_true_labels = []
    train_people_cited_predicted_labels = []
    for article in train_dicts:
        prediction_results = predict_authors(classifier, train_dataset, article['article'])
        if prediction_results:
            true_labels, predicted_labels = prediction_results
            train_people_cited_true_labels += true_labels
            train_people_cited_predicted_labels += predicted_labels

    train_labels = zip(train_people_cited_true_labels, train_people_cited_predicted_labels)
    accuracy = sum([true == predicted for true, predicted in train_labels]) / len(train_people_cited_true_labels)
    precision, recall, f1, _ = precision_recall_fscore_support(train_people_cited_true_labels,
                                                               train_people_cited_predicted_labels,
                                                               zero_division=0,
                                                               average='binary')
    train_people_cited_scores = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
    }
    train_author_set_results.add_scores(train_people_cited_scores)

    test_people_cited_true_labels = []
    test_people_cited_predicted_labels = []
    test_authors_per_article = []
    for article in test_dicts:
        prediction_results = predict_authors(classifier, test_dataset, article['article'])
        all_names = article['article'].people['people']
        if prediction_results:
            true_labels, predicted_labels = prediction_results
            test_people_cited_true_labels += true_labels
            test_people_cited_predicted_labels += predicted_labels
            people_cited = [name for name, label in zip(all_names, true_labels) if label == 1]
            people_predicted = [name for name, label in zip(all_names, predicted_labels) if label == 1]
            test_authors_per_article.append({
                'all': all_names,
                'cited': people_cited,
                'predicted': people_predicted
            })

    test_labels = zip(test_people_cited_true_labels, test_people_cited_predicted_labels)
    accuracy = sum([true == predicted for true, predicted in test_labels]) / len(test_people_cited_true_labels)
    precision, recall, f1, _ = precision_recall_fscore_support(test_people_cited_true_labels,
                                                               test_people_cited_predicted_labels,
                                                               zero_division=0,
                                                               average='binary')
    test_people_cited_scores = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
    }
    test_author_set_results.add_scores(test_people_cited_scores)

    return train_results, test_results, train_author_set_results, test_author_set_results, test_authors_per_article
