import numpy as np
from collections import Counter
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import KFold
from sklearn.preprocessing import PolynomialFeatures

from backend.ml.sgd import train, evaluate
from backend.ml.helpers import print_scores
from backend.db_management import load_labeled_articles, load_quote_authors
from backend.ml.quote_attribution_dataset import QuoteAttributionDataset, subset, subset_ovo, \
    attribution_train_loader, attribution_test_loader
from backend.ml.quote_detection_dataset import QuoteDetectionDataset


def load_data(nlp, cue_verbs, ovo, poly):
    train_articles, train_sentences, _, _ = load_labeled_articles(nlp)
    quote_detection_dataset = QuoteDetectionDataset(train_articles, train_sentences, cue_verbs, poly)
    train_dicts, _ = load_quote_authors(nlp)
    quote_attribution_dataset = QuoteAttributionDataset(train_dicts, quote_detection_dataset, cue_verbs, ovo, poly)

    train_article_ids = np.array(list(map(lambda a: a['article'].id, train_dicts)))

    return train_article_ids, quote_attribution_dataset


def predict_quote_author(trained_model, quote_features):
    """
    Uses a trained model to predict which Named Entity in an article is the true author of a quote.

    :param trained_model: SGDClassifier
        The classifier to use to predict the author of the quote.
    :param quote_features: list(np.array)
        The features for each mention in the article.
    :return: int
        The index of the predicted speaker in the mentions of the article.
    """

    best_mention = 0
    best_proba = 0

    # Evaluate features all speakers in the article
    for index, mention_features in enumerate(quote_features):
        prediction = trained_model.predict_proba(mention_features.reshape((1, -1)))
        if prediction[0, 1] > best_proba:
            best_mention = index
            best_proba = prediction[0, 1]

    return best_mention


def predict_quote_author_ovo(trained_model, quote_features, num_mentions):
    """
    Uses a trained model to predict which Named Entity in an article is the true author of a quote.

    :param trained_model: SGDClassifier
        The classifier to use to predict the author of the quote.
    :param quote_features: list(np.array)
        The features for each mention in the article.
    :return: int
        The index of the predicted speaker in the mentions of the article.
    """

    mention_wins = num_mentions * [0]

    for m1_index in range(num_mentions):
        for m2_index in range(num_mentions):
            if m1_index != m2_index:
                m1_m2_features_index = m1_index * (num_mentions - 1) + m2_index - int(m1_index < m2_index)
                m1_m2_features = quote_features[m1_m2_features_index]
                prediction = trained_model.predict_proba(m1_m2_features.reshape((1, -1)))
                mention_wins[m1_index] += prediction[0, 0]
                mention_wins[m2_index] += prediction[0, 1]

    return np.argmax(mention_wins)


def predict_authors(trained_model, dataset, articles, ovo=False):
    """
    Predicts the speaker for each quote in a list of articles.

    :param trained_model: SGDClassifier
        The classifier to use to predict the author of the quote.
    :param dataset: QuoteAttributionDataset
        The dataset containing the article for which we want to predict the author of a quote.
    :param articles: list(int)
        The unique id of the articles for which we want to predict the speaker of each quote.
    """
    true_speaker_indices = []
    predicted_speaker_indices = []
    for article_id in articles:
        start_index, _, num_quotes, num_mentions = dataset.get_article_features(article_id)
        for quote_id in range(num_quotes):
            quote_features, quote_labels = dataset.get_quote_mention_features(article_id, quote_id)
            if ovo:
                true_speaker = -1
                m_index = 0
                while true_speaker == -1 and m_index < num_mentions:
                    if quote_labels[m_index] == 1:
                        true_speaker = m_index
                    else:
                        m_index += 1
                true_speaker_indices.append(true_speaker)
                predicted_speaker = predict_quote_author_ovo(trained_model, quote_features, num_mentions)
            else:
                true_speaker = -1
                for mention_index, label in enumerate(quote_labels):
                    if label == 1:
                        if true_speaker >= 0:
                            print('error! found 2 speakers in the same sentence')
                        true_speaker = mention_index
                true_speaker_indices.append(true_speaker)
                predicted_speaker = predict_quote_author(trained_model, quote_features)
            predicted_speaker_indices.append(predicted_speaker)

    return true_speaker_indices, predicted_speaker_indices


def evaluate_quote_attribution(nlp, cue_verbs, cv_folds=5, ovo=False):
    """
    Evaluates the quote attribution model.
    """
    poly = PolynomialFeatures(2, interaction_only=False)
    print('Creating dataset...')
    article_ids, attribution_dataset = load_data(nlp, cue_verbs, ovo, poly)

    kf = KFold(n_splits=cv_folds)
    max_iter = 200
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
    train_accuracies = []
    test_accuracies = []
    print('Performing cross-validation...')
    for train_indices, test_indices in kf.split(article_ids):
        classifier = SGDClassifier(loss='log', alpha=0.1, penalty='l2')

        train_ids = article_ids[train_indices]
        test_ids = article_ids[test_indices]
        if ovo:
            train_dataset = subset_ovo(attribution_dataset, train_ids)
            test_dataset = subset_ovo(attribution_dataset, test_ids)
        else:
            train_dataset = subset(attribution_dataset, train_ids)
            test_dataset = subset(attribution_dataset, test_ids)

        train_loader = attribution_train_loader(train_dataset, batch_size=len(train_dataset))
        test_loader = attribution_test_loader(test_dataset)

        classifier, loss, accuracy = train(classifier, train_loader, max_iter)

        train_loader = attribution_test_loader(train_dataset)
        train_scores = evaluate(classifier, train_loader)
        for key in train_results.keys():
            train_results[key].append(train_scores[key])
        test_scores = evaluate(classifier, test_loader)
        for key in test_results.keys():
            test_results[key].append(test_scores[key])

        true_speakers, predicted_speaker = predict_authors(classifier, attribution_dataset, train_ids, ovo)
        train_accuracies.append(np.sum(np.equal(true_speakers, predicted_speaker)) / len(true_speakers))

        true_speakers, predicted_speaker = predict_authors(classifier, attribution_dataset, test_ids, ovo)
        test_accuracies.append(np.sum(np.equal(true_speakers, predicted_speaker)) / len(true_speakers))

    train_averages = {}
    test_averages = {}
    for key in train_results.keys():
        train_averages[key] = round(sum(train_results[key])/len(train_results[key]), 3)
        test_averages[key] = round(sum(test_results[key]) / len(test_results[key]), 3)

    print(print_scores('Average Training Results', train_averages))
    print(print_scores('Average Test Results', test_averages))

    print(f'\n    Accuracy in speaker prediction:\n'
          f'        Training: {round(sum(train_accuracies)/len(train_accuracies), 3)}\n'
          f'        Test:     {round(sum(test_accuracies)/len(test_accuracies), 3)}\n')
