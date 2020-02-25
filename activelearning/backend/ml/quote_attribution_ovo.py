import numpy as np

from backend.ml.feature_extraction import extract_ovo_features
from backend.ml.helpers import find_true_author_index

from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import KFold
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import precision_recall_fscore_support


""" File containing all methods to build a model for one vs one quote attribution. """


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

        # Create features for all speakers in the article
        other_quotes = article_dict['quotes'][:i] + article_dict['quotes'][i + 1:]
        q_attribution_features = extract_ovo_features(nlp, article_dict['article'], i, other_quotes, cue_verbs)

        all_features = []
        labels = []

        for neg_sample_index in range(len(mentions)):
            # If the negative sample is equal to the true author, replace it with the weasel feature.
            if neg_sample_index == true_mention_index:
                neg_sample_index = len(mentions)

            if np.random.random() > 0.5:
                # Speaker 1 is the true speaker
                features = q_attribution_features[true_mention_index, neg_sample_index, :]
                label = 0
            else:
                # Speaker 2 is the true speaker
                features = q_attribution_features[neg_sample_index, true_mention_index, :]
                label = 1

            all_features.append(features)
            labels.append(label)

        if X is None:
            X = np.array(all_features)
            y = np.array(labels)
        else:
            X = np.concatenate((X, np.array(all_features)), axis=0)
            y = np.concatenate((y, np.array(labels)), axis=0)

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


def evaluate_ovo_quote_attribution(nlp, data, cue_verbs, cv_folds=5):
    """
    Evaluates different classifiers for one vs one speaker prediction. This is the performance of the model when
    it's given two speakers (the true span that is the author of the quote and a negative sample) and has to choose which
    one is the true speaker.

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
    kf = KFold(n_splits=cv_folds)
    poly = PolynomialFeatures(2, interaction_only=True)

    print('        Loading data')
    article_features = np.array([create_article_features(nlp, article, cue_verbs) for article in data])

    model_scores = {}
    for name, classifier in CLASSIFIERS.items():

        print(f'        Evaluating {name}')

        model_scores[name] = {
            'train_precision': 0,
            'train_recall': 0,
            'train_f1': 0,
            'test_precision': 0,
            'test_recall': 0,
            'test_f1': 0,
        }

        folds = 0
        for train, test in kf.split(data):
            print(f'          Fold {folds}')
            folds += 1

            print(f'            Seperating into train and test ({len(train)} train, {len(test)} test articles)')
            train_data, test_data = article_features[train], article_features[test]

            X_train = None
            y_train = None
            for a in train_data:
                if X_train is None:
                    X_train = a[0]
                    y_train = a[1]
                else:
                    X_train = np.concatenate((X_train, a[0]), axis=0)
                    y_train = np.concatenate((y_train, a[1]), axis=0)

            X_test = None
            y_test = None
            for a in test_data:
                if X_test is None:
                    X_test = a[0]
                    y_test = a[1]
                else:
                    X_test = np.concatenate((X_test, a[0]), axis=0)
                    y_test = np.concatenate((y_test, a[1]), axis=0)

            print('            Feature Expansion')
            X_train = poly.fit_transform(X_train)
            X_test = poly.fit_transform(X_test)

            print('            Training')
            classifier.fit(X_train, y_train)

            print('            Evaluating')
            y_train_pred = classifier.predict(X_train)
            y_test_pred = classifier.predict(X_test)

            train_p, train_r, train_f, _ = precision_recall_fscore_support(y_train, y_train_pred, average='macro')
            test_p, test_r, test_f, _ = precision_recall_fscore_support(y_test, y_test_pred, average='macro')

            model_scores[name]['train_precision'] += train_p
            model_scores[name]['train_recall'] += train_r
            model_scores[name]['train_f1'] += train_f
            model_scores[name]['test_precision'] += test_p
            model_scores[name]['test_recall'] += test_r
            model_scores[name]['test_f1'] += test_f

        for key in model_scores[name].keys():
            model_scores[name][key] = round(model_scores[name][key]/cv_folds, 3)

    return model_scores


def train_ovo_quote_attribution(model, nlp, data, cue_verbs):
    """
    Trains a classifier to choose which speaker between two of them are more likely.

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
    poly = PolynomialFeatures(2, interaction_only=True)
    X = poly.fit_transform(X)
    classifier = CLASSIFIERS[model]
    classifier.fit(X, y)
    return classifier


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
    predicted_authors = []
    for i, sent_index in enumerate(article_dict['quotes']):

        # Create features for all speakers in the article
        other_quotes = article_dict['quotes'][:i] + article_dict['quotes'][i + 1:]
        q_attribution_features = extract_ovo_features(nlp, article_dict['article'], i, other_quotes, cue_verbs)

        num_mentions = q_attribution_features.shape[0]
        mentions_wins = num_mentions * [0]

        for m in range(num_mentions):
            for n in range(num_mentions):
                if m != n:
                    features = q_attribution_features[m, n, :].reshape(1, -1)
                    features = poly.fit_transform(features)
                    if use_proba:
                        prediction = trained_model.predict_proba(features)
                        mentions_wins[m] += prediction[0, 0]
                        mentions_wins[n] += prediction[0, 1]
                    else:
                        prediction = trained_model.predict(features)[0]
                        mentions_wins[m] += 1 - prediction
                        mentions_wins[n] += prediction
        speaker_index = np.argmax(mentions_wins)
        predicted_authors.append(speaker_index)

    return predicted_authors


def evaluate_ovo_speaker_prediction(nlp, data, cue_verbs, cv_folds=5):
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

    print('            Loading data')
    article_features = np.array([create_article_features(nlp, article, cue_verbs) for article in data])

    for name, classifier in CLASSIFIERS.items():

        print(f'            Evaluating {name}')

        model_scores[name] = {
            'train_accuracy': 0,
            'test_accuracy': 0,
        }

        folds = 0
        for train, test in kf.split(data):
            print(f'              Fold {folds}')
            folds += 1

            print('                Seperating into train and test')
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


            print('                Feature Expansion')
            X_train = poly.fit_transform(X_train)

            print('                Training')
            classifier.fit(X_train, y_train)

            print('                Evaluating on Training Set')
            train_acc = 0
            for a in np.array(data)[train]:
                mentions = a['article'].people['mentions']
                y_train = [find_true_author_index(author_index, mentions) for author_index in a['authors']]
                y_train_pred = predict_article_speakers(classifier, nlp, a, cue_verbs, use_proba=False)
                train_acc += np.sum(np.equal(y_train, y_train_pred)) / len(y_train)
            train_acc /= len(np.array(data)[train])

            print('                Evaluating on Test Set')
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
