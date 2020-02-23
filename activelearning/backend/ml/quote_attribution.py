import numpy as np

from backend.ml.feature_extraction import extract_speaker_features

from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import cross_validate, KFold
from sklearn.preprocessing import PolynomialFeatures


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
    for index, mention in enumerate(mentions):
        if mention['start'] <= reported_end and mention['end'] >= reported_start:
            return index
    return -1


def create_input_matrix(nlp, articles, sentence_ids, labels, cue_verbs):
    """
    Creates the input matrix from the raw data.

    :param nlp:
        spaCy.Language The language model used to tokenize the text
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
    y = None
    # All features
    all_features = []
    # The index of the true mention in the article
    true_mention_indices = []
    for i, article in enumerate(articles):
        mentions = article.people['mentions']
        for j, sent_index in enumerate(sentence_ids[i]):
            # List of indices of the tokens of the true author of the quote
            true_author = labels[i][j]
            true_mention_index = find_true_author_index(true_author, mentions)
            if true_mention_index >= 0:

                # Create features for all speakers in the article
                other_quotes = sentence_ids[i][:j] + sentence_ids[i][j + 1:]
                speaker_features = extract_speaker_features(nlp, article, j, other_quotes, cue_verbs)
                all_features.append(speaker_features)
                true_mention_indices.append(true_mention_index)

                # Sample from the remaining mentions.
                neg_sample_index = np.random.randint(len(mentions) - 1)
                if neg_sample_index == true_mention_index:
                    neg_sample_index = len(mentions) - 1

                if np.random.random() > 0.5:
                    # Speaker 1 is the true speaker
                    features = speaker_features[true_mention_index, neg_sample_index, :]
                    label = np.array([0])
                else:
                    # Speaker 2 is the true speaker
                    features = speaker_features[neg_sample_index, true_mention_index, :]
                    label = np.array([1])

                features = features.reshape(1, -1)
                if X is None:
                    X = features
                    y = label
                else:
                    X = np.concatenate((X, features), axis=0)
                    y = np.concatenate((y, label), axis=0)

            # else:
            # TODO: What to do when the author isn't a named entity? Just ignore it?

    return X, y, np.array(all_features), np.array(true_mention_indices)


def train_ovo_quote_attribution(model, nlp, articles, sentence_ids, labels, cue_verbs):
    """
    Trains a classifier to choose which speaker between two of them are more likely.

    :param model: string
        The model to use for classification. One of {'L1 logistic', 'L2 logistic', 'Linear SVC'}.
    :param nlp:
        spaCy.Language The language model used to tokenize the text
    :param articles: list(Article)
        A list of fully labeled articles
    :param sentence_ids: list(list(int))
        A list of sentences containing quotes that are in the training set, for each article in the articles list
    :param labels: list(list(list(int)))
        A list of authors (a list of token indices) for training sentences that contain quotes for each article
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return: sklearn.linear_model
        The trained model to predict probabilities for sentences.
    """
    X, y, _, _ = create_input_matrix(nlp, articles, sentence_ids, labels, cue_verbs)
    poly = PolynomialFeatures(2, interaction_only=True)
    X = poly.fit_transform(X)
    classifier = CLASSIFIERS[model]
    classifier.fit(X, y)
    return classifier


def evaluate_ovo_quote_attribution(nlp, articles, sentence_ids, labels, cue_verbs, cv_folds=5):
    """
    Evaluates different classifiers for one vs one speaker prediction. This is the performance of the model when
    it's given two quotes (the true span that is the author of the quote and a negative sample) and has to choose which
    one is the true speaker.

    :param nlp:
        spaCy.Language The language model used to tokenize the text
    :param articles: list(Article)
        A list of fully labeled articles
    :param sentence_ids: list(list(int))
        A list of sentences containing quotes that are in the training set, for each article in the articles list
    :param labels: list(list(list(int)))
        A list of authors (a list of token indices) for training sentences that contain quotes for each article
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
    X, y, _, _ = create_input_matrix(nlp, articles, sentence_ids, labels, cue_verbs)
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


def predict_speakers(trained_model, all_features):
    """
    Given a trained model for one vs one speaker prediction, predicts the speaker for each quote amongst all speakers in
    the article.

    :param trained_model: sklearn.linear_model
        A trained model to predict which speaker is more likely
    :param all_features: np.array
        An array of shape (N, _) where N is the number of quotes. Element n in this array has shape (m, m, d), where
        m is the number of different mentions in the article containing quote n, and d is the number of features for
        each one vs one prediction.
    :return: np.array
        Array of shape (N, ), where element n is the index of the predicted speaker for quote n in all_features.
    """
    poly = PolynomialFeatures(2, interaction_only=True)
    mention_indices = []
    for quote_speaker_features in all_features:
        num_mentions = quote_speaker_features.shape[0]
        mentions_wins = num_mentions * [0]
        for i in range(num_mentions):
            for j in range(num_mentions):
                if i != j:
                    features = quote_speaker_features[i, j, :].reshape(1, -1)
                    features = poly.fit_transform(features)
                    prediction = trained_model.predict_proba(features)
                    mentions_wins[i] += prediction[0, 0]
                    mentions_wins[j] += prediction[0, 1]
        speaker_index = np.argmax(mentions_wins)
        mention_indices.append(speaker_index)
    return np.array(mention_indices)


def evaluate_speaker_prediction(nlp, articles, sentence_ids, labels, cue_verbs, cv_folds=5):
    """
    Evaluates different classifiers on predicting the correct speaker, and returns their performance. Creates the input
    matrix from the raw data.

    :param nlp:
        spaCy.Language The language model used to tokenize the text
    :param articles: list(Article)
        A list of fully labeled articles
    :param sentence_ids: list(list(int))
        A list of sentences containing quotes that are in the training set, for each article in the articles list
    :param labels: list(list(list(int)))
        A list of authors (a list of token indices) for training sentences that contain quotes for each article
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
    X, y, features, true_mention_indices = create_input_matrix(nlp, articles, sentence_ids, labels, cue_verbs)
    kf = KFold(n_splits=cv_folds)
    poly = PolynomialFeatures(2, interaction_only=True)
    model_scores = {}
    for name, classifier in CLASSIFIERS.items():
        train_precision = 0
        test_precision = 0
        for train, test in kf.split(X):
            X_train, X_test, y_train, y_test = X[train], X[test], y[train], y[test]
            X_train = poly.fit_transform(X_train)
            classifier.fit(X_train, y_train)
            mention_indices = predict_speakers(classifier, features)

            train_labels = true_mention_indices[train]
            train_predictions = mention_indices[train]

            test_labels = true_mention_indices[test]
            test_predictions = mention_indices[test]

            train_precision += np.sum(np.equal(train_labels, train_predictions)) / len(train_labels)
            test_precision += np.sum(np.equal(test_labels, test_predictions)) / len(test_labels)

        model_scores[name] = {
            'training': train_precision/cv_folds,
            'test': test_precision/cv_folds,
        }
    return model_scores




































