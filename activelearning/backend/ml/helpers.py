import numpy as np


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
    reported_start = true_author[0]
    reported_end = true_author[-1]
    for index, mention in enumerate(mentions):
        if mention['start'] <= reported_end and mention['end'] >= reported_start:
            return index
    return -1


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


def parse_sentence(nlp, article, sentence_id):
    """

    :param article:
    :param sentence_id:
    :return:
    """
    quote_start = 0
    if sentence_id > 0:
        quote_start = article.sentences['sentences'][sentence_id - 1] + 1
    quote_end = article.sentences['sentences'][sentence_id]
    q_in_quotes = article.in_quotes['in_quotes'][quote_start:quote_end + 1]
    q_doc = nlp(''.join(article.tokens['tokens'][quote_start:quote_end + 1]))
    return q_doc, q_in_quotes
