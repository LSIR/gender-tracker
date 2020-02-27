import numpy as np
from collections import Counter
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import precision_recall_fscore_support, log_loss
from sklearn.model_selection import KFold
from sklearn.preprocessing import PolynomialFeatures

from backend.db_management import load_labeled_articles, load_quote_authors
from backend.ml.quote_attribution_dataset import QuoteAttributionDataset, subset, \
    attribution_train_loader, attribution_test_loader
from backend.ml.quote_detection_dataset import QuoteDetectionDataset


def load_data(nlp, cue_verbs, ovo, poly):
    print('\nCreating quote attribution dataset...')
    train_articles, _ = load_labeled_articles()
    quote_detection_dataset = QuoteDetectionDataset(train_articles, cue_verbs, nlp, poly)
    train_dicts, _ = load_quote_authors()
    quote_attribution_dataset = QuoteAttributionDataset(train_dicts, quote_detection_dataset, nlp, cue_verbs, ovo, poly)

    train_article_ids = np.array(list(map(lambda a: a['article'].id, train_dicts)))

    return train_article_ids, quote_attribution_dataset


def train(classifier, dataloader, max_iter):
    """
    Trains a classifier using SGD.
    TODO: Implement early stopping, check that I don't need to touch learning rates.

    :param classifier: SGDClassifier
        The classifier to train.
    :param dataloader: Dataloader
        The dataloader containing the data to train the classifier on.
    :param max_iter: int
        The number of epochs to run SGD for.
    :return: SGDClassifier, list(float), list(float)
        * the trained classifier
        * the loss after each dataload
        * the accuracy after each dataload
    """
    loss = []
    accuracy = []
    for n in range(max_iter):
        for X, y in dataloader:
            classifier.partial_fit(X, y, classes=np.array([0, 1]))
            y_pred = classifier.predict_proba(X)
            loss.append(log_loss(y, y_pred))
            accuracy.append(classifier.score(X, y))

    return classifier, loss, accuracy


def evaluate(classifier, dataloader):
    """


    :param classifier: SGDClassifier
        The classifier to train.
    :param dataloader: Dataloader
        The dataloader containing the data to evaluate the classifier on.
    :return: dict
        A dictionary containing the scores of the classifier on the dataset contained in the dataloader. Keys:
            * 'accuracy': the model's accuracy
            * 'precision': the model's precision
            * 'recall': the model's recall
            * 'f1': the model's f1
    """
    scores = {
        'accuracy': 0,
        'precision': 0,
        'recall': 0,
        'f1': 0,
    }
    for X, y in dataloader:
        y_pred = classifier.predict(X)
        scores['accuracy'] += classifier.score(X, y)
        precision, recall, f1, _ = precision_recall_fscore_support(y, y_pred, average='macro')
        scores['precision'] += precision
        scores['recall'] += recall
        scores['f1'] += f1

    for key in scores.keys():
        scores[key] /= len(dataloader)

    return scores


def print_scores(title, scores):
    """
    Prints the scores for a model to the console.

    :param title: string
        The title to print.
    :param scores: dict
        A dictionary containing the scores of the classifier on the dataset contained in the dataloader. Keys:
            * 'accuracy': the model's accuracy
            * 'precision': the model's precision
            * 'recall': the model's recall
            * 'f1': the model's f1
    :return:
    """
    return f'\n    {title}:\n' + \
           f'        accuracy:  {scores["accuracy"]}\n' + \
           f'        precision: {scores["precision"]}\n' + \
           f'        recall:    {scores["recall"]}\n' + \
           f'        f1 score:  {scores["f1"]}\n'


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


def evaluate_speaker_prediction(trained_model, dataset, articles):
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


def evaluate_quote_attribution(nlp, cue_verbs, cv_folds=5):
    """
    Evaluates the quote attribution model.
    """
    poly = PolynomialFeatures(2, interaction_only=True)
    article_ids, attribution_dataset = load_data(nlp, cue_verbs, False, poly)
    print(f'Labeled article ids: {article_ids}')

    print(f'Quote Attribution')
    kf = KFold(n_splits=cv_folds)
    max_iter = 50
    folds = 0
    for train_indices, test_indices in kf.split(article_ids):
        print(f'\n  Fold {folds}')
        folds += 1
        classifier = SGDClassifier(loss='log', penalty='l2')

        print(f'\n  Splitting datasets into subsets')
        train_ids = article_ids[train_indices]
        test_ids = article_ids[test_indices]
        train_dataset = subset(attribution_dataset, train_ids)
        test_dataset = subset(attribution_dataset, test_ids)

        print(f'    Training articles: {len(train_ids)}, ids: {train_ids}')
        print(f'    Testing articles:  {len(test_ids)}, ids: {test_ids}')
        train_loader = attribution_train_loader(train_dataset, batch_size=len(train_dataset))
        test_loader = attribution_test_loader(test_dataset)

        classifier, loss, accuracy = train(classifier, train_loader, max_iter)

        train_loader = attribution_test_loader(train_dataset)
        print_scores('Train Results', evaluate(classifier, train_loader))
        print_scores('Test Results', evaluate(classifier, test_loader))

        true_speakers, predicted_speaker = evaluate_speaker_prediction(classifier, attribution_dataset, train_ids)
        print(f'\n    Training Accuracy: {np.sum(np.equal(true_speakers, predicted_speaker)) / len(true_speakers)}')
        print('    True speaker counts:     ', dict(Counter(true_speakers)))
        print('    Predicted speaker counts:', dict(Counter(predicted_speaker)))
        true_speakers, predicted_speaker = evaluate_speaker_prediction(classifier, attribution_dataset, test_ids)
        print(f'\n    Testing Accuracy: {np.sum(np.equal(true_speakers, predicted_speaker)) / len(true_speakers)}')
        print('    True speaker counts:     ', dict(Counter(true_speakers)))
        print('    Predicted speaker counts:', dict(Counter(predicted_speaker)))
