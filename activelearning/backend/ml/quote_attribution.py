import numpy as np

from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import KFold
from sklearn.preprocessing import PolynomialFeatures

from backend.ml.helpers import author_full_name, extract_speaker_names, evaluate_speaker_extraction
from backend.ml.scoring import Results
from backend.ml.sgd import train, evaluate
from backend.db_management import load_labeled_articles, load_quote_authors
from backend.ml.quote_attribution_dataset import QuoteAttributionDataset, subset, subset_ovo, \
    attribution_loader
from backend.ml.quote_detection_dataset import QuoteDetectionDataset


def load_data(nlp, cue_verbs, ovo, poly):
    """
    Loads the datasets to perform quote attribution.

    :param nlp: spaCy.Language
        The language model used to tokenize the text.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param ovo: boolean
        Whether to load the One vs One model or not.
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
    train_articles, train_sentences, _, _ = load_labeled_articles(nlp)
    quote_detection_dataset = QuoteDetectionDataset(train_articles, train_sentences, cue_verbs, poly)
    train_dicts, _ = load_quote_authors(nlp)
    quote_attribution_dataset = QuoteAttributionDataset(train_dicts, quote_detection_dataset, cue_verbs, ovo, poly)

    return np.array(train_dicts), quote_attribution_dataset


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
    :param num_mentions: int
        The number of mentions in the article containing the quote.
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


def predict_authors(trained_model, dataset, article, ovo=False):
    """
    Predicts the speaker for each quote in a list of articles.

    :param trained_model: SGDClassifier
        The classifier to use to predict the author of the quote.
    :param dataset: QuoteAttributionDataset
        The dataset containing the article for which we want to predict the author of a quote.
    :param article: models.Article
        The article for which we want to predict the speaker of each quote.
    :param ovo: boolean
        Whether to load the One vs One model or not.
    :return: np.array(int), np.array(int)
        The true and predicted author indices.
    """
    true_speaker_indices = []
    predicted_speaker_indices = []
    start_index, _, num_quotes, num_mentions = dataset.get_article_features(article.id)
    for quote_id in range(num_quotes):
        quote_features, quote_labels = dataset.get_quote_mention_features(article.id, quote_id)
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

    true_names = extract_speaker_names(article, true_speaker_indices)
    predicted_names = extract_speaker_names(article, predicted_speaker_indices)
    precision, recall = evaluate_speaker_extraction(true_names, predicted_names)

    return true_speaker_indices, predicted_speaker_indices, precision, recall


def predict_authors_list(trained_model, dataset, articles, ovo=False):
    """
    Predicts the speaker for each quote in a list of articles.

    :param trained_model: SGDClassifier
        The classifier to use to predict the author of the quote.
    :param dataset: QuoteAttributionDataset
        The dataset containing the article for which we want to predict the author of a quote.
    :param articles: list(int)
        The unique id of the articles for which we want to predict the speaker of each quote.
    :param ovo: boolean
        Whether to load the One vs One model or not.
    :return: np.array(int), np.array(int)
        The true and predicted author indices.
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


def evaluate_quote_attribution(penalty, nlp, cue_verbs, cv_folds=5, ovo=False):
    """
    Evaluates the quote attribution model.

    :param penalty: string
        One of {'l1', 'l2}. The penalty to use for training
    :param nlp: spaCy.Language
        The language model used to tokenize the text.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param cv_folds: int
        The number of cross-validation folds to perform.
    :param ovo: boolean
        Whether to load the One vs One model or not.
    """
    poly = PolynomialFeatures(2, interaction_only=False)
    print('    Creating dataset...')
    article_dicts, attribution_dataset = load_data(nlp, cue_verbs, ovo, poly)

    print(f'    Feature dimensionality: {attribution_dataset.feature_dimensionality }')

    kf = KFold(n_splits=cv_folds)
    max_iter = 200

    train_results = Results()
    test_results = Results()

    train_accuracies = []
    train_precision = []
    train_recall = []
    test_accuracies = []
    test_precision = []
    test_recall = []
    print('    Performing cross-validation...')

    for alpha in [0.001, 0.01, 0.1, 1]:
        print(f'\n        Evaluating with regularization term: {alpha}')
        for train_indices, test_indices in kf.split(article_dicts):
            classifier = SGDClassifier(loss='log', alpha=alpha, penalty=penalty)

            train_articles = article_dicts[train_indices]
            train_ids = list(map(lambda a: a['article'].id, train_articles))

            test_articles = article_dicts[test_indices]
            test_ids = list(map(lambda a: a['article'].id, test_articles))

            if ovo:
                train_dataset = subset_ovo(attribution_dataset, train_ids)
                test_dataset = subset_ovo(attribution_dataset, test_ids)
            else:
                train_dataset = subset(attribution_dataset, train_ids)
                test_dataset = subset(attribution_dataset, test_ids)

            train_loader = attribution_loader(train_dataset, train=True, batch_size=len(train_dataset))
            test_loader = attribution_loader(test_dataset, train=False, batch_size=len(test_dataset))

            classifier, loss, accuracy = train(classifier, train_loader, max_iter)

            train_loader = attribution_loader(train_dataset, train=False, batch_size=len(train_dataset))
            train_results.add_scores(evaluate(classifier, train_loader))
            test_results.add_scores(evaluate(classifier, test_loader))

            for article in train_articles:
                y, y_pred, precision, recall = predict_authors(classifier, attribution_dataset, article['article'], ovo)
                train_accuracies.append(np.sum(np.equal(y, y_pred))/len(y))
                train_precision.append(precision)
                train_recall.append(recall)

            for article in test_articles:
                y, y_pred, precision, recall = predict_authors(classifier, attribution_dataset, article['article'], ovo)
                test_accuracies.append(np.sum(np.equal(y, y_pred))/len(y))
                test_precision.append(precision)
                test_recall.append(recall)

        print('          Average Training Results')
        print(train_results.average_score())
        print('          Average Test Results')
        print(test_results.average_score())

        print(f'\n          Accuracy in speaker prediction:\n'
              f'            Training: {round(sum(train_accuracies)/len(train_accuracies), 3)}\n'
              f'            Test:     {round(sum(test_accuracies)/len(test_accuracies), 3)}\n')

        print(f'\n          Predicting authors in articles:\n'
              f'            Training Precision: {round(sum(train_precision)/len(train_precision), 3)}\n'
              f'            Training Recall:    {round(sum(train_recall)/len(train_recall), 3)}\n'
              f'            Test Precision:     {round(sum(test_precision)/len(test_precision), 3)}\n'
              f'            Test Recall:        {round(sum(test_recall)/len(test_recall), 3)}\n')
