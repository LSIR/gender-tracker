from django.core.exceptions import ObjectDoesNotExist
from backend.models import Article, UserLabel
from backend.helpers import paragraph_sentences

""" File containing all methods to select and format user labelling tasks. """

MIN_USER_LABELS = 4

ARTICLE_LOADS = 10

COUNT_THRESHOLD = 3

CONFIDENCE_THRESHOLD = 80


def form_sentence_json(article, paragraph_id, sentence_id):
    """
    Given an article and some sentence indices in the article, forms a dict containing the key-value pairs article_id
    (int), a paragraph_id (int), a sentence_id ([int]), data (list[string]) and  task ('sentence').

    If a sentence needs to be labelled, sentence_id is a list of a least one integer, and data is a list of individual
    tokens (words).

    :param article: Article.
        The article that needs to be labelled
    :param paragraph_id: int.
        The index of the paragraph that contains the sentences that need to be labelled
    :param sentence_id: list(int).
        The indices of the sentences in the Article that need to be labelled
    :return: dict.
        A dict containing article_id, paragraph_id, sentence_id, data and task keys
    """
    tokens = article.tokens['tokens']
    if sentence_id[0] == 0:
        start_token = 0
    else:
        start_token = article.sentences['sentences'][sentence_id[0] - 1] + 1
    end_token = article.sentences['sentences'][sentence_id[-1]]
    return {
        'article_id': article.id,
        'paragraph_id': paragraph_id,
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
        'paragraph_id': paragraph_id,
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

    if sentence_id <= 0 or sentence_id > len(sentence_ends):
        return {'data': [], 'first_sentence': 0, 'last_sentence': 0}

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

    if sentence_id < 0 or sentence_id >= len(sentence_ends) - 1:
        return {'data': [], 'first_sentence': 0, 'last_sentence': 0}

    first_sentence = 0
    last_sentence = paragraph_ends[0]
    paragraph_index = 0
    while sentence_id > first_sentence:
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


def load_hardest_articles(n):
    """
    Loads the hardest articles to classify in the database, in terms of the confidence in the
    answers.

    :param n: int.
        The number of articles to load from the database
    :return: list(Article).
        The n hardest articles to classify.
    """
    # Return only articles that don't have enough labels for all sentences
    return Article.objects.filter(label_counts__min_label_counts__lt=MIN_USER_LABELS) \
               .order_by('confidence__min_confidence', 'id')[:n]


def quote_start_sentence(sentence_ends, in_quote, token_index):
    """
    Given the index of the first token of a sentence, which is inside quotation marks, returns the index of the sentence
    where the quotation mark started.

    :param sentence_ends: list(int).
        The list of the last token of each sentence
    :param in_quote: list(int)..
        The list of in_quote tokens
    :param token_index: int.
        The index of the token in the quote
    :return: int.
        The index of the sentence containing the first token in the quote
    """
    while in_quote[token_index] == 1 and token_index > 0:
        token_index -= 1
    sentence_index = 1
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
    sentence_index = len(sentence_ends) - 1
    while token_index <= sentence_ends[sentence_index]:
        sentence_index -= 1
    return sentence_index + 1


def request_labelling_task(session_id):
    """
    Finds a sentence or paragraph that needs to be labelled, and that doesn't already have a label with the given
    session_id. If the list of sentence_indices is empty, then the whole paragraph needs to be labelled. Otherwise,
    the sentence(s) need to be labelled.

    :param session_id: int.
        The user's session id
    :return: dict.
        A dict containing article_id, paragraph_id, sentence_id, data and task keys
    """
    session_labels = UserLabel.objects.filter(session_id=session_id)
    articles = load_hardest_articles(ARTICLE_LOADS)
    for article in articles:
        annotated_sentences = [user_label.sentence_index for user_label in session_labels.filter(article=article)]
        label_counts = article.label_counts['label_counts']
        confidences = article.confidence['confidence']
        sentence_ends = article.sentences['sentences']
        prev_par_end = -1
        # p is the index of the last sentence in paragraph i
        for (i, p) in enumerate(article.paragraphs['paragraphs']):
            # Lowest confidence in the whole paragraph
            min_conf = min([conf for conf in confidences[prev_par_end + 1:p + 1]])

            # For high enough confidences, annotate the whole paragraph
            if min_conf >= CONFIDENCE_THRESHOLD \
                    and label_counts[prev_par_end + 1] < COUNT_THRESHOLD \
                    and (prev_par_end + 1) not in annotated_sentences:
                return form_paragraph_json(article, i)

            # For all sentences in the paragraph, check if they can be annotated by the user
            for j in range(prev_par_end + 1, p + 1):
                if label_counts[j] < COUNT_THRESHOLD and j not in annotated_sentences:
                    # List of sentence indices to label
                    labelling_task = [j]
                    # Checks that the sentence's last token is inside quotes, in which case the next sentence would
                    # also need to be returned
                    sent_end = sentence_ends[j]
                    if article.in_quotes['in_quotes'][sent_end] == 1:
                        last_sent = quote_end_sentence(sentence_ends, article.in_quotes['in_quotes'], sent_end)
                        labelling_task = list(range(labelling_task[0], last_sent + 1))
                    return form_sentence_json(article, i, labelling_task)
            prev_par_end = p
    return None
