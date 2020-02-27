import csv

import numpy as np
import spacy
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import KFold

from backend.db_management import load_labeled_articles
from backend.ml.quote_detection_dataset import QuoteDetectionDataset, detection_train_loader, \
    detection_test_loader, subset


def set_custom_boundaries(doc):
    """ Custom boundaries so that spaCy doesn't split sentences at ';' or at '-[A-Z]'. """
    for token in doc[:-1]:
        if token.text == ";":
            doc[token.i+1].is_sent_start = False
        if token.text == "-" and token.i != 0:
            doc[token.i].is_sent_start = False
    return doc


def load_data(nlp, cue_verbs):
    print('\nCreating quote detection dataset...')
    train_articles, _ = load_labeled_articles()
    quote_detection_dataset = QuoteDetectionDataset(train_articles, cue_verbs, nlp)

    train_article_ids = np.array(list(map(lambda a: a.id, train_articles)))

    return train_article_ids, quote_detection_dataset


def evaluate_quote_detection(nlp, cue_verbs, cv_folds=5):
    article_ids, quote_detection_dataset = load_data(nlp, cue_verbs)
    print(f'Labeled article ids: {article_ids}')

    print(f'Quote Detection')
    kf = KFold(n_splits=cv_folds)
    n_iter = 20
    folds = 0
    for train, test in kf.split(article_ids):
        print(f'\n  Fold {folds}')
        folds += 1
        classifier = SGDClassifier(loss='log', penalty='l2')
        print(f'\n  Splitting datasets into subsets')
        train_ids = article_ids[train]
        test_ids = article_ids[test]
        train_dataset = subset(quote_detection_dataset, train_ids)
        test_dataset = subset(quote_detection_dataset, test_ids)

        print(f'    Training articles: {len(train_ids)}, ids: {train_ids}')
        print(f'    Testing articles:  {len(test_ids)}, ids: {test_ids}')
        train_loader = detection_train_loader(train_dataset, batch_size=1)
        test_loader = detection_test_loader(test_dataset)
        for n in range(n_iter):
            for features, labels in train_loader:
                classifier.partial_fit(features, labels, classes=np.array([0, 1]))

        X_test, y_test = [(batch[0], batch[1]) for batch in test_loader][0]
        y_test_pred = classifier.predict(X_test)
        test_p, test_r, test_f, _ = precision_recall_fscore_support(y_test, y_test_pred, average='macro')
        print(f'\n    Test Results:\n'
              f'        precision: {test_p}\n'
              f'        recall:    {test_r}\n'
              f'        f1 score:  {test_f}\n')

    return quote_detection_dataset


