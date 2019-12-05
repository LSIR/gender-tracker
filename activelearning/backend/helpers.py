from backend.models import Article, UserLabel
from django.core.exceptions import ObjectDoesNotExist


##############################################################################################
# Helpers
##############################################################################################


def paragraph_sentences(article, paragraph_index):
    """
    Finds the index of the first and last sentence, for a paragraph.

    :param article: Article.
        The article that contains the paragraph.
    :param paragraph_index: int.
        The index of the paragraph
    :return: (int, int).
        The indices of the first and last sentence in the paragraph.
    """
    par_ends = article.paragraphs['paragraphs']
    if paragraph_index == 0:
        first_sent = 0
    else:
        first_sent = par_ends[paragraph_index - 1] + 1
    last_sent = par_ends[paragraph_index]
    return first_sent, last_sent


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
    label_counts = [[label, labels.count(label)] for label in set(labels)]
    author_counts = [[author, authors.count(author)] for author in set(authors)]
    max_label_count = max(label_counts, key=lambda x: x[1])
    max_author_count = max(author_counts, key=lambda x: x[1])
    return max_label_count[0], max_author_count[0], (max_label_count[1] + max_author_count[1]) / (2 * len(labels))


def is_sentence_labelled(article, sentence_id, min_users, min_consensus):
    """
    Determines if there is a consensus among enough users so that the label is considered correct. If a consensus
    exists, returns the labels and authors.

    :param article: Article.

    :param sentence_id: int.

    :param min_users: int.

    :param min_consensus: float.

    :return: boolean.

    """
    sentence_labels = UserLabel.objects.filter(article=article, sentence_index=sentence_id)
    admin_label = [label for label in sentence_labels.filter(admin_label=True)]
    if len(admin_label) > 0:
        admin_label = admin_label[0]
        return admin_label.labels['labels'], admin_label.author_index['author_index']
    else:
        labels = [label.labels['labels'] for label in sentence_labels]
        authors = [label.author_index['author_index'] for label in sentence_labels]
        if len(labels) > min_users:
            labels, authors, consensus = label_consensus(labels, authors)
            if consensus > min_consensus:
                return labels, authors

    return None


def is_article_labelled(article, min_users, min_consensus):
    """
    Determines if all labels in the article have a consensus label. If that's the case, returns them. Otherwise
    returns None.

    :param article: Article.

    :param min_users: int.

    :param min_consensus: float.

    :return: boolean.

    """
    all_labels = []
    all_authors = []
    for s in range(len(article.sentences['sentences'])):
        data = is_sentence_labelled(article, s, min_users, min_consensus)
        if data is None:
            return None
        else:
            labels, authors = data
            all_labels.append(labels)
            all_authors.append(authors)

    return all_labels, all_authors


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
