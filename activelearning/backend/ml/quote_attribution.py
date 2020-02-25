import numpy as np

from backend.ml.feature_extraction import extract_quote_features, extract_single_speaker_features
from backend.ml.helpers import find_true_author_index, parse_sentence, balance_classes

from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import cross_validate, KFold
from sklearn.preprocessing import PolynomialFeatures


""" File containing all methods to build a model for one vs all quote attribution. """


""" The models used for quote attribution """
CLASSIFIERS = {
    'L1 logistic': LogisticRegression(C=2, penalty='l1', solver='liblinear', max_iter=10000, multi_class='ovr'),
    'L2 logistic': LogisticRegression(C=2, penalty='l2', solver='liblinear', max_iter=10000, multi_class='ovr'),
    'Linear SVC': SVC(kernel='linear', C=2, probability=True, random_state=0),
}


def create_article_features(nlp, article_dict, cue_verbs):
    """
    Creates the input matrix for the quotes in a single article.

    :param nlp:
        spaCy.Language The language model used to tokenize the text
    :param article_dict: list(dict)
        A dicts containing information about the fully labeled article. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return: np.array, np.array
        * An array of shape (N, m + 1, m + 1, d) where N is the number of quotes, m is the number of different mentions
        in the article containing quote n, and d is the number of features for each one vs one prediction. It has m + 1
        dimensions because the last one is when there is no named entity that is the author of the quote.
        * An array of shape (N, 1) where N is the number of quotes. Each value is the index of the true author of each
        quote. If the value is -1, then the quote's author isn't a named entity.
    """
    X = None
    y = None
    mentions = article_dict['article'].people['mentions']
    for i, sent_index in enumerate(article_dict['quotes']):
        # List of indices of the tokens of the true author of the quote
        true_author = article_dict['authors'][i]
        true_mention_index = find_true_author_index(true_author, mentions)

        # Create features for all mentions in the article
        other_quotes = article_dict['quotes'][:i] + article_dict['quotes'][i + 1:]

        q_doc, q_in_quotes = parse_sentence(nlp, article_dict['article'], sent_index)
        quote_features = extract_quote_features(q_doc, cue_verbs, q_in_quotes)

        # Create features for all speakers in the article
        for index, mention in enumerate(mentions):
            ne_features = extract_single_speaker_features(nlp, article_dict['article'], sent_index, other_quotes,
                                                          mention, cue_verbs)
            features = np.concatenate((quote_features, ne_features), axis=0).reshape(1, -1)

            label = np.array([0])
            if index == true_mention_index:
                label = np.array([1])

            if X is None:
                X = features
                y = label
            else:
                X = np.concatenate((X, features), axis=0)
                y = np.concatenate((y, label), axis=0)

        # Create weasel feature:
        weasel_feature = np.zeros((1, X.shape[1]))
        weasel_feature[0, :len(quote_features)] = quote_features
        label = np.array([0])
        if true_mention_index == -1:
            label = np.array([1])
        X = np.concatenate((X, weasel_feature), axis=0)
        y = np.concatenate((y, label), axis=0)

    return X, y


def create_input_matrix(nlp, data, cue_verbs):
    """
    Creates the input matrix from the raw data.

    :param nlp:
        spaCy.Language The language model used to tokenize the text
    :param data: list(dict)
        A list of dicts containing information about fully labeled articles. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return: np.array, np.array
        * An array of shape (N, _) where N is the number of quotes. Element n in this array has shape (m + 1, m + 1, d),
        where m is the number of different mentions in the article containing quote n, and d is the number of features
        for each one vs one prediction. It has m + 1 dimensions because the last one is when there is no named entity
        that is the author of the quote.
        * An array of shape (N, 1) where N is the number of quotes. Each value is the index of the true author of each
        quote. If the value is -1, then the quote's author isn't a named entity.
    """
    X = None
    y = None
    for sample in data:
        article_X, article_y = create_article_features(nlp, sample, cue_verbs)
        if X is None:
            X = np.array(article_X)
            y = np.array(article_y)
        else:
            X = np.concatenate((X, np.array(article_X)), axis=0)
            y = np.concatenate((y, np.array(article_y)), axis=0)
    return X, y


def train_quote_attribution(model, nlp, data, cue_verbs):
    """
    Trains a classifier to learn if a speaker is likely to be the author of a quote or not.

    :param model: string
        The model to use for classification. One of {'L1 logistic', 'L2 logistic', 'Linear SVC'}.
    :param nlp: spaCy.Language
        The language model used to tokenize the text
    :param data: list(dict)
        A list of dicts containing information about fully labeled articles. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return: sklearn.linear_model
        The trained model to predict probabilities for sentences.
    """
    X, y = create_input_matrix(nlp, data, cue_verbs)
    X, y = balance_classes(X, y)
    poly = PolynomialFeatures(2, interaction_only=True)
    X = poly.fit_transform(X)
    classifier = CLASSIFIERS[model]
    classifier.fit(X, y)
    return classifier


def evaluate_quote_attribution(nlp, data, cue_verbs, cv_folds=5):
    """
    Evaluates different classifiers for one vs all speaker prediction. This is the performance of the model when
    it's given on speaker and has to predict if it's the true speaker or not.

    :param nlp: spaCy.Language
        The language model used to tokenize the text
    :param data: list(dict)
        A list of dicts containing information about fully labeled articles. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param cv_folds: int
        The number of folds in cross-validation.
    :return: dict
        * keys: model names
        * values: dict
            * keys: 'test_accuracy', 'test_precision_macro', 'test_f1_macro'
            * values: the (test) accuracy/precision/f1 score.
    """
    X, y = create_input_matrix(nlp, data, cue_verbs)
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


def predict_article_speakers(trained_model, nlp, article_dict, cue_verbs, use_proba=False):
    """
    Given a trained model for one vs one speaker prediction, predicts the speaker for each quote amongst all speakers in
    the article.

    :param trained_model: sklearn.linear_model
        A trained model to predict which speaker is more likely
    :param nlp:
        spaCy.Language The language model used to tokenize the text
    :param article_dict: list(dict)
        A dicts containing information about the fully labeled article. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return:
    """
    poly = PolynomialFeatures(2, interaction_only=True)
    mentions = article_dict['article'].people['mentions']
    predicted_authors = []
    for i, sent_index in enumerate(article_dict['quotes']):
        # List of indices of the tokens of the true author of the quote
        true_author = article_dict['authors'][i]
        true_mention_index = find_true_author_index(true_author, mentions)

        # Create features for all mentions in the article
        other_quotes = article_dict['quotes'][:i] + article_dict['quotes'][i + 1:]

        q_doc, q_in_quotes = parse_sentence(nlp, article_dict['article'], sent_index)
        quote_features = extract_quote_features(q_doc, cue_verbs, q_in_quotes)

        best_mention = 0
        best_mention_proba = 0

        # Evaluate features all speakers in the article
        for index, mention in enumerate(mentions):
            ne_features = extract_single_speaker_features(nlp, article_dict['article'], sent_index, other_quotes,
                                                          mention, cue_verbs)
            features = np.concatenate((quote_features, ne_features), axis=0).reshape(1, -1)
            features = poly.fit_transform(features)
            prediction = trained_model.predict_proba(features)
            if prediction[0, 1] > best_mention_proba:
                best_mention = index
                best_mention_proba = prediction[0, 1]

        # Create weasel feature:
        weasel_feature = np.zeros(features.shape)
        weasel_feature[0, :len(quote_features)] = quote_features
        prediction = trained_model.predict_proba(weasel_feature)
        if prediction[0, 1] > best_mention_proba:
            best_mention = -1

        predicted_authors.append(best_mention)

    return predicted_authors


def evaluate_speaker_prediction(nlp, data, cue_verbs, cv_folds=5):
    """
    Evaluates different classifiers on predicting the correct speaker, and returns their performance. Creates the input
    matrix from the raw data.

    :param nlp: spaCy.Language
        The language model used to tokenize the text
    :param data: list(dict)
        A list of dicts containing information about fully labeled articles. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param cv_folds: int
        The number of folds in cross-validation.
    :return: dict
        * keys: model names
        * values: dict
            * keys: 'training', 'test'
            * values: the percentage of training (test) quotes that are attributed to the correct speaker.
    """
    kf = KFold(n_splits=cv_folds)
    poly = PolynomialFeatures(2, interaction_only=True)
    model_scores = {}

    print('        Loading data')
    article_features = np.array([create_article_features(nlp, article, cue_verbs) for article in data])

    for name, classifier in CLASSIFIERS.items():

        print(f'        Evaluating {name}')

        model_scores[name] = {
            'train_accuracy': 0,
            'test_accuracy': 0,
        }

        folds = 0
        for train, test in kf.split(data):
            folds += 1
            train_data = article_features[train]

            X_train = None
            y_train = None
            for a in train_data:
                if X_train is None:
                    X_train = a[0]
                    y_train = a[1]
                else:
                    X_train = np.concatenate((X_train, a[0]), axis=0)
                    y_train = np.concatenate((y_train, a[1]), axis=0)

            X_train = poly.fit_transform(X_train)
            classifier.fit(X_train, y_train)

            train_acc = 0
            for a in np.array(data)[train]:
                mentions = a['article'].people['mentions']
                y_train = [find_true_author_index(author_index, mentions) for author_index in a['authors']]
                y_train_pred = predict_article_speakers(classifier, nlp, a, cue_verbs, use_proba=False)
                train_acc += np.sum(np.equal(y_train, y_train_pred)) / len(y_train)
            train_acc /= len(np.array(data)[train])

            test_acc = 0
            for a in np.array(data)[test]:
                mentions = a['article'].people['mentions']
                y_test = [find_true_author_index(author_index, mentions) for author_index in a['authors']]
                y_test_pred = predict_article_speakers(classifier, nlp, a, cue_verbs, use_proba=False)
                test_acc += np.sum(np.equal(y_test, y_test_pred)) / len(y_test)
            test_acc /= len(np.array(data)[test])

            model_scores[name]['train_accuracy'] += train_acc
            model_scores[name]['test_accuracy'] += test_acc

        for key in model_scores[name].keys():
            model_scores[name][key] = round(model_scores[name][key] / cv_folds, 3)

    return model_scores
