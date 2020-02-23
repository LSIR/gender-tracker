import numpy as np

from backend.ml.feature_extraction import extract_person_mentions, extract_speaker_features_ovo

from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import cross_validate, KFold
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
    for index, (m_start, m_end) in enumerate(mentions):
        if m_start <= reported_end and m_end >= reported_start:
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
    # The index of the true mention in the article
    true_mention_indices = None
    for i, article in enumerate(articles):
        people, mentions, full_names = extract_person_mentions(article)
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
                    s1 = mentions[true_mention_index]
                    s2 = mentions[neg_sample_index]
                    label = np.array([0])
                else:
                    # Speaker 2 is the true speaker
                    s1 = mentions[neg_sample_index]
                    s2 = mentions[true_mention_index]
                    label = np.array([1])

                features = extract_speaker_features_ovo(nlp, article, sent_index, other_quotes, s1, s2, cue_verbs)
                features = features.reshape(1, -1)
                true_index = np.array([true_mention_index])
                if X is None:
                    X = features
                    y = label
                    true_mention_indices = true_index
                else:
                    X = np.concatenate((X, features), axis=0)
                    y = np.concatenate((y, label), axis=0)
                    true_mention_indices = np.concatenate((true_mention_indices, true_index), axis=0)

            # else:
            # TODO: What to do when the author isn't a named entity? Just ignore it?

    return X, y, true_mention_indices


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
    X, y, _ = create_input_matrix(nlp, articles, sentence_ids, labels, cue_verbs)
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
    :return:
    """
    X, y, _ = create_input_matrix(nlp, articles, sentence_ids, labels, cue_verbs)
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


def predict_speakers(trained_model, nlp, articles, sentence_ids, cue_verbs):
    """
    Computes probabilities that each sentence contains a quote.

    :param trained_model: sklearn.linear_model
        A trained model to predict probabilities for sentences.
    :param nlp:
        spaCy.Language The language model used to tokenize the text
    :param articles: list(Article)
        A list of articles
    :param sentence_ids: list(list(int))
        A list of sentences containing quotes, for each article in the articles list
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return: np.array(int), list(list(string, string))
        The (speaker_mention, full_name) for each quote in each article
    """
    mention_indices = []
    speakers = []
    poly = PolynomialFeatures(2, interaction_only=True)
    for i, article in enumerate(articles):
        article_speakers = []
        people, mentions, full_names = extract_person_mentions(article)
        for j, sent_index in enumerate(sentence_ids[i]):
            mentions_wins = len(mentions) * [0]
            other_quotes = sentence_ids[i][:j] + sentence_ids[i][j + 1:]
            for s1_index, s1 in enumerate(mentions):
                for s2_index, s2 in enumerate(mentions):
                    if s1_index != s2_index:
                        features = extract_speaker_features_ovo(nlp, article, sent_index, other_quotes, s1, s2, cue_verbs)
                        features = features.reshape(1, -1)
                        features = poly.fit_transform(features)
                        prediction = trained_model.predict_proba(features)
                        mentions_wins[s1_index] += prediction[0, 0]
                        mentions_wins[s2_index] += prediction[0, 1]
            speaker_index = np.argmax(mentions_wins)
            mention_indices.append(speaker_index)
            article_speakers.append((mentions[speaker_index].text, full_names[speaker_index]))
        speakers.append(article_speakers)
    return np.array(mention_indices), speakers


def evaluate_speaker_prediction(nlp, articles, sentence_ids, labels, cue_verbs, cv_folds=5):
    """
    Evaluates different classifiers, and returns their performance.

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
    :param cv_folds: int
        The number of folds in cross-validation.
    :return:
    """
    X, y, true_mention_indices = create_input_matrix(nlp, articles, sentence_ids, labels, cue_verbs)
    poly = PolynomialFeatures(2, interaction_only=True)
    X = poly.fit_transform(X)
    kf = KFold(n_splits=cv_folds)
    model_scores = {}
    for name, classifier in CLASSIFIERS.items():
        train_precision = 0
        test_precision = 0
        for train, test in kf.split(X):
            X_train, X_test, y_train, y_test = X[train], X[test], y[train], y[test]
            classifier.fit(X_train, y_train)
            mention_indices, _ = predict_speakers(classifier, nlp, articles, sentence_ids, cue_verbs)

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




































