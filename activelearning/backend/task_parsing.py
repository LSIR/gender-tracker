from django.core.exceptions import ObjectDoesNotExist
from .helpers import add_user_labels_to_db, paragraph_sentences
from .models import Article


def label_edges(article, paragraph_index, sentence_indices):
    """
    Finds the index of the first and last token and the index of the first and last sentence, for a list of sentences
    or a paragraph.

    :param article: Article.
        The article that contains the paragraph.
    :param paragraph_index: int.
        The index of the paragraph
    :param sentence_indices: list(int).
        The indices of the sentences. Empty list if the task is for an entire paragraph
    :return: dictionary:
        'token': (int, int). The indices of the first and last token in the paragraph.
        'sentence': (int, int). The indices of the first and last sentence in the paragraph.
    """
    sent_ends = article.sentences['sentences']
    if len(sentence_indices) == 0:
        first_sent, last_sent = paragraph_sentences(article, paragraph_index)
    else:
        first_sent = sentence_indices[0]
        last_sent = sentence_indices[-1]

    if first_sent == 0:
        first_token = 0
    else:
        first_token = sent_ends[first_sent - 1] + 1
    last_token = sent_ends[last_sent]
    return {
        'token': (first_token, last_token),
        'sentence': (first_sent, last_sent),
    }


def add_labels_to_database(user_id, article_id, paragraph_index, sentence_indices, tags, authors):
    """
    Computes the indices of tokens that are authors and cleans the user tags to only contain words that are in the
    quotes, and not the tags for authors.

    :param user_id: string.
        The id of the user who created the labels.
    :param article_id: int.
        The id of the article where the user performed a labelling task
    :param paragraph_index: int.
        The index of the paragraph in the article where the user performed a labelling task
    :param sentence_indices: list(int).
        The indices of the sentences the user labelled, and empty if the user labelled a paragraph.
    :param tags: list(int).
        The user tags
    :param authors: list(int).
        The relative position of the author of the quote, if there is one.
    :return: list(list(int), list(int), list(int)).
        The list(token label) for each labelled sentence, the list of sentence indices, and the list of absolute
        position of the author of this quote.
    """
    try:
        article = Article.objects.get(id=article_id)
    except ObjectDoesNotExist:
        return None

    edges = label_edges(article, paragraph_index, sentence_indices)
    first_token, last_token = edges['token']
    first_sent, last_sent = edges['sentence']

    # Transform relative index to absolute index
    author_indices = []
    for index in authors:
        author_indices.append(first_token + index)

    # Split the tags into labels for each sentence
    sentence_indices = range(first_sent, last_sent + 1)
    sent_ends = article.sentences['sentences']
    sentence_labels = []
    sentence_start = first_token
    first_tag_index = 0
    for index in sentence_indices:
        last_tag_index = first_tag_index + (sent_ends[index] - sentence_start)
        sentence_labels.append(tags[first_tag_index:last_tag_index + 1])
        first_tag_index = last_tag_index + 1
        sentence_start = sent_ends[index] + 1

    for i in range(len(sentence_labels)):
        add_user_labels_to_db(article_id, user_id, sentence_labels[i], sentence_indices[i], author_indices)
