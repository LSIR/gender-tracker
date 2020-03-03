from sklearn.metrics import precision_recall_fscore_support, log_loss
import numpy as np
from sklearn.model_selection import KFold
from sklearn.linear_model import SGDClassifier
from backend.ml.scoring import Results


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
            loss.append(log_loss(y, y_pred, labels=np.array([0, 1])))
            accuracy.append(classifier.score(X, y))

    return classifier, loss, accuracy


def cross_validate(split_ids, dataset, subset, dataloader, alpha, max_iter, cv_folds):
    """
    Performs cross-validation for a model on a dataset.

    :param split_ids: list(int)
        The ids of the articles in the dataset. Used to split them into subsets for cross-validation.
    :param dataset: torch.utils.data.Dataset
        The dataset to use for cross-validation.
    :param subset: function
        The method, with parameters (dataset, ids), used to split the dataset into two subsets using article ids.
    :param dataloader: function
        The method, with parameters (dataset, train, batch_size) that returns a Dataloader.
    :param alpha: float
        The regularization term.
    :param max_iter: int
        The maximum number of epochs to train on.
    :param cv_folds: int
        The number of cross-validation folds to perform.
    :return: Results, Results
        The results on the training and test sets
    """
    kf = KFold(n_splits=cv_folds)

    train_results = Results()
    test_results = Results()

    for train_indices, test_indices in kf.split(split_ids):
        # Create the model
        classifier = SGDClassifier(loss='log', alpha=alpha, penalty='l2')

        # Split the dataset into train and test
        train_ids = split_ids[train_indices]
        train_dataset = subset(dataset, train_ids)
        train_loader = dataloader(train_dataset, train=True, batch_size=len(train_dataset))

        test_ids = split_ids[test_indices]
        test_dataset = subset(dataset, test_ids)
        test_loader = dataloader(test_dataset, train=False, batch_size=len(test_dataset))

        classifier, loss, accuracy = train(classifier, train_loader, max_iter)

        train_loader = dataloader(train_dataset, train=False, batch_size=len(train_dataset))
        train_results.add_scores(evaluate(classifier, train_loader))
        test_results.add_scores(evaluate(classifier, test_loader))

    return train_results, test_results


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
        precision, recall, f1, _ = precision_recall_fscore_support(y, y_pred, zero_division=0, average='binary')
        scores['precision'] += precision
        scores['recall'] += recall
        scores['f1'] += f1

    for key in scores.keys():
        scores[key] /= len(dataloader)

    return scores
