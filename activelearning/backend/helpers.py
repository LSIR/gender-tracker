from backend.models import Article, UserLabel
from django.core.exceptions import ObjectDoesNotExist


##############################################################################################
# Helpers
##############################################################################################


def label_consensus(labels, authors):
    """
    Computes the (label, author) pair that is most common in the user labels, as well as the percentage of responses
    that contain them

    :param labels: list(list(int)).
        The list of tags that each user reported.
    :param authors: list(list(int)).
        The list of author indices that each user reported.
    :return: Tuple(list(int), list(int), float).
        list(int): The labels for each token.
        list(int): The author indices.
        float: A consensus between 0 and 1.
    """
    if len(labels) == 0:
        return [], [], 0
    # Set of tuples as lists can't be hashed in Python
    label_sets = set(tuple(i) for i in labels)
    author_sets = set(tuple(i) for i in authors)
    label_counts = [[label, labels.count(list(label))] for label in label_sets]
    author_counts = [[author, authors.count(list(author))] for author in author_sets]
    max_label_count = max(label_counts, key=lambda x: x[1])
    max_author_count = max(author_counts, key=lambda x: x[1])
    return list(max_label_count[0]), list(max_author_count[0]),\
        (max_label_count[1] + max_author_count[1]) / (2 * len(labels))


##############################################################################################
# Learning
##############################################################################################


def change_confidence(article_id, confidences):
    """
    Edits the Article database to reflect that the trained model has changed his confidence level that each sentence is
    or isn't reported speech.

    :param article_id: int.
        The id of the article to edit
    :param confidences: list(int).
        The confidence (in [0, 100]) the trained model has for each sentence.
    :return: int.
        The minimum confidence this article has in a sentence, or -1 if the article couldn't be added to the database.
    """
    try:
        article = Article.objects.get(id=article_id)
    except ObjectDoesNotExist:
        return None

    old_conf = article.confidence['confidence']
    min_conf = min(confidences)
    if len(confidences) == len(old_conf) and min_conf >= 0 and max(confidences) <= 100:
        new_conf = {
            'confidence': confidences,
            'min_confidence': min_conf,
        }
        article.confidence = new_conf
        article.save()
        return min_conf
    return None


def quote_start_sentence(sentence_ends, in_quote, token_index):
    """
    Given the index of the first token of a sentence, which is inside quotation marks, returns the index of the sentence
    where the quotation mark started.

    :param sentence_ends: list(int).
        The list of the last token of each sentence
    :param in_quote: list(int).
        The list of in_quote tokens
    :param token_index: int.
        The index of the token in the quote
    :return: int.
        The index of the sentence containing the first token in the quote
    """
    while token_index >= 0 and in_quote[token_index] == 1:
        token_index -= 1
    token_index += 1
    sentence_index = 0
    while token_index > sentence_ends[sentence_index]:
        sentence_index += 1
    return sentence_index


def quote_end_sentence(sentence_ends, in_quote, token_index):
    """
    Given the index of the last token of a sentence, which is inside quotation marks, returns the index of the sentence
    where the quotation mark ends.

    :param sentence_ends: list(int).
        The list of the last token of each sentence
    :param in_quote: list(int).
        The list of in_quote tokens
    :param token_index: int.
        The index of the last token in the sentence
    :return: int.
        The index of the sentence containing the last token in the quote
    """
    while token_index < len(in_quote) and in_quote[token_index] == 1:
        token_index += 1
    token_index -= 1
    sentence_index = len(sentence_ends) - 1
    while sentence_index >= 0 and token_index <= sentence_ends[sentence_index]:
        sentence_index -= 1
    return sentence_index + 1
