import numpy as np
from joblib import dump, load


def find_true_author_index(true_author, mentions):
    """
    Finds the index of the mention that is the author of the quote. As there might be little differences in between what
    spaCy sees as Named Entities and what people see as Named Entities, we're just looking for an Named Entity that
    overlaps with the tag.

    :param true_author: list(int)
        The index of the tokens of the true_author.
    :param mentions: list(dict)
        The mentions of PER named entities in the article, saved as dicts with keys 'start' (the index of the first
        token in the named entity), 'end' (the index of the last token in the named entity), 'name' (the text of the
        named entity) and 'full_name' (the longest form of that person's name found in the article).
    :return: int
        The index of the mention in the list of mentions, or -1 if the true author isn't a named entity.
    """
    if len(true_author) == 0:
        return -1
    reported_start = true_author[0]
    reported_end = true_author[-1]
    for index, mention in enumerate(mentions):
        if mention['start'] <= reported_end and mention['end'] >= reported_start:
            return index
    return -1


def author_full_name(article, author_index):
    """
    Determines the full name of someone cited in an article, given the index of the named entity in the article.

    :param article: models.Article
        The article containing the author
    :param author_index: int
        The index of the author in the list of mentions.
    :return: string
        The name of the author of the quote.
    """
    if author_index < 0 or author_index >= len(article.people['mentions']):
        return None
    return article.people['mentions'][author_index]['full_name']


def author_full_name_no_db(article_mentions, author_index):
    """
    Determines the full name of someone cited in an article, given the index of the named entity in the article.

    :param article_mentions: ...
        Article.people['mentions']
    :param author_index: int
        The index of the author in the list of mentions.
    :return: string
        The name of the author of the quote.
    """
    if author_index < 0 or author_index >= len(article_mentions):
        return None
    return article_mentions[author_index]['full_name']


def extract_speaker_names(article, author_indices):
    """
    Given an article and the indices of named entities in the article that are quoted in it, extracts their full names.

    :param article: models.Article
        The article containing the author
    :param author_indices: list(int)
        The index of the author in the list of mentions.
    :return: Set(string)
        The full names of people quoted in the article.
    """
    speakers = set()
    for i in author_indices:
        full_name = author_full_name(article, i)
        if full_name is not None and full_name not in speakers:
            speakers.add(full_name)
    return speakers


def evaluate_speaker_extraction(true_names, predicted_names):
    """
    Computes the precision and recall for an article, given the true people cited and the predictions from a model.

    :param true_names: set(string)
        The names as given by user labels
    :param predicted_names: set(string)
        The names as predicted by a model
    :return: float, float
        The precision and recall.
    """
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    for name in true_names:
        if name in predicted_names:
            true_positives += 1
        else:
            false_negatives += 1

    for name in predicted_names:
        if name not in true_names:
            false_positives += 1

    if true_positives + false_positives == 0:
        precision = 1
    else:
        precision = true_positives/(true_positives + false_positives)

    if true_positives + false_negatives == 0:
        recall = 1
    else:
        recall = true_positives/(true_positives + false_negatives)

    return precision, recall


def balance_classes(X, y):
    """
    Given the input matrices for an unbalanced classification task (where one class is present much more often than the
    other in the data), balances the classes so they both have the same number of samples by sub-sampling from the class
    that's more present.

    :param X: np.ndarray
        The input vectors.
    :param y: np.ndarray
        The labels.
    :return: np.ndarray, np.ndarray
        X, y: the input vectors and labels.
    """
    # Indices where the label is 0 (no reported speech is present)
    is_not_quote = (y == 0).nonzero()[0]
    # Indices where the label is 1 (reported speech is present)
    is_quote = (y == 1).nonzero()[0]
    # Takes random indices from the class most present, and all indices from the one least present
    if len(is_quote) < len(is_not_quote):
        subsample = np.random.choice(is_not_quote, size=len(is_quote), replace=False)
        indices = np.sort(np.concatenate((subsample, is_quote)))
    else:
        subsample = np.random.choice(is_quote, size=len(is_not_quote), replace=False)
        indices = np.sort(np.concatenate((subsample, is_not_quote)))
    # Only keeps some of the values
    sampled_y = np.take(y, indices)
    sampled_X = np.take(X, indices, axis=0)
    return sampled_X, sampled_y


def save_model(classifier, filepath):
    """

    :param classifier:
    :param filepath:
    :return:
    """
    dump(classifier, filepath)


def load_model(filepath):
    """

    :param filepath:
    :return:
    """
    return load(filepath)
