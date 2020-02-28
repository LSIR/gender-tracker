from sklearn.metrics import precision_recall_fscore_support, log_loss
import numpy as np


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
    Evaluates a trained classifier on data.

    :param classifier: SGDClassifier
        The classifier to evaluate.
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
