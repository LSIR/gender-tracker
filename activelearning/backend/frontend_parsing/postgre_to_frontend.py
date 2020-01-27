from django.core.exceptions import ObjectDoesNotExist

from backend.models import Article

""" File containing all methods to select and format user labelling tasks. """


def form_sentence_json(article, sentence_id):
    """
    Given an article and some sentence indices in the article, forms a dict containing the key-value pairs article_id
    (int), a paragraph_id (int), a sentence_id ([int]), data (list[string]) and  task ('sentence').

    If a sentence needs to be labelled, sentence_id is a list of a least one integer, and data is a list of individual
    tokens (words).

    :param article: Article.
        The article that needs to be labelled
    :param sentence_id: list(int).
        The indices of the sentences in the Article that need to be labelled
    :return: dict.
        A dict containing article_id, paragraph_id, sentence_id, data and task keys
    """
    if len(sentence_id) == 0:
        return {
            'article_id': article.id,
            'sentence_id': [],
            'data': [],
            'task': 'sentence'
        }
    tokens = article.tokens['tokens']
    start_token = 0
    if sentence_id[0] > 0:
        start_token = article.sentences['sentences'][sentence_id[0] - 1] + 1
    end_token = article.sentences['sentences'][sentence_id[-1]]
    return {
        'article_id': article.id,
        'sentence_id': sentence_id,
        'data': tokens[start_token:end_token + 1],
        'task': 'sentence'
    }


def form_paragraph_json(article, paragraph_id):
    """
    Given an article and some sentence indices in the article, forms a dict containing the key-value pairs article_id
    (int), a paragraph_id (int), a sentence_id ([int]), data (list[string]) and  task ('paragraph').

    Sentence_id is an empty list, and data is a list containing a single string, which is the content of the entire
    paragraph.

    :param article: Article.
        The article that needs to be labelled
    :param paragraph_id: int.
        The index of the paragraph in the Article that needs to be labelled
    :return: dictionary.
        A dict containing article_id, paragraph_id, sentence_id, data and task keys
    """
    tokens = article.tokens['tokens']
    par_ends = article.paragraphs['paragraphs']
    sent_ends = article.sentences['sentences']
    if paragraph_id == 0:
        start_token = 0
        start_sent = 0
    else:
        start_sent = par_ends[paragraph_id - 1] + 1
        start_token = sent_ends[start_sent - 1] + 1
    end_token = sent_ends[par_ends[paragraph_id]]
    end_sent = par_ends[paragraph_id]
    return {
        'article_id': article.id,
        'sentence_id': list(range(start_sent, end_sent + 1)),
        'data': tokens[start_token:end_token + 1],
        'task': 'paragraph'
    }


def load_paragraph_above(article_id, sentence_id):
    """
    Finds the lists of tokens for a paragraph above a given sentence. If the sentence is in a paragraph below the
    requested paragraph, returns the whole paragraph. If the sentence is the first of the paragraph, returns the
    paragraph above.

    :param article_id: int.
        The id of the Article of which we want the tokens for a paragraph.
    :param sentence_id: int.
        The index of the sentence for which we want the tokens above.
    :return: dict.
        data: list(string). The tokens in paragraph paragraph_id.
        paragraph: int. The index of the paragraph returned.
    """
    try:
        article = Article.objects.get(id=article_id)
    except ObjectDoesNotExist:
        return None

    tokens = article.tokens['tokens']
    paragraph_ends = article.paragraphs['paragraphs']
    sentence_ends = article.sentences['sentences']

    # If the sentence_id is 0, no data can be loaded
    if not (0 < sentence_id < len(sentence_ends)):
        return {'data': [], 'first_sentence': -1, 'last_sentence': -1}

    first_sentence = 0
    last_sentence = paragraph_ends[0]
    paragraph_index = 0
    while sentence_id > last_sentence + 1:
        paragraph_index += 1
        first_sentence = last_sentence + 1
        last_sentence = paragraph_ends[paragraph_index]

    last_sentence = min(sentence_id - 1, last_sentence)

    if first_sentence == 0:
        first_token = 0
    else:
        first_token = sentence_ends[first_sentence - 1] + 1
    last_token = sentence_ends[last_sentence]
    return {
        'data': tokens[first_token:last_token + 1],
        'first_sentence': first_sentence,
        'last_sentence': last_sentence,
    }


def load_paragraph_below(article_id, sentence_id):
    """
    Finds the lists of tokens for a paragraph below a given sentence. If the sentence is in a paragraph above the
    requested paragraph, returns the whole paragraph. Returns an empty list of tokens if the end of the article has
    been reached. If the sentence is the last of the paragraph, returns th paragraph below.

    :param article_id: int.
        The id of the Article of which we want the tokens for a paragraph.
    :param sentence_id: int.
        The index of the sentence for which we want the tokens below.
    :return: dict.
        data: list(string). The tokens in paragraph paragraph_id.
        paragraph: int. The index of the paragraph returned.
    """
    try:
        article = Article.objects.get(id=article_id)
    except ObjectDoesNotExist:
        return None

    tokens = article.tokens['tokens']
    paragraph_ends = article.paragraphs['paragraphs']
    sentence_ends = article.sentences['sentences']

    # If the sentence_id is the last sentence of the article, no text below can be loaded
    if not (0 <= sentence_id < len(sentence_ends) - 1):
        return {'data': [], 'first_sentence': -1, 'last_sentence': -1}

    first_sentence = 0
    last_sentence = paragraph_ends[0]
    paragraph_index = 0
    while sentence_id >= last_sentence:
        paragraph_index += 1
        first_sentence = last_sentence + 1
        last_sentence = paragraph_ends[paragraph_index]

    first_sentence = max(first_sentence, sentence_id + 1)

    if first_sentence == 0:
        first_token = 0
    else:
        first_token = sentence_ends[first_sentence - 1] + 1
    last_token = sentence_ends[last_sentence]
    return {
        'data': tokens[first_token:last_token + 1],
        'first_sentence': first_sentence,
        'last_sentence': last_sentence,
    }
