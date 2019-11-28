from backend.models import Article, UserLabel
from django.core.exceptions import ObjectDoesNotExist

""" File containing all methods to select and format user labelling tasks. """

MIN_USER_LABELS = 4

ARTICLE_LOADS = 5

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
    else:
        start_sent = par_ends[paragraph_id - 1] + 1
        start_token = sent_ends[start_sent - 1] + 1
    end_token = sent_ends[par_ends[paragraph_id]]
    return {
        'article_id': article.id,
        'paragraph_id': paragraph_id,
        'sentence_id': [],
        'data': tokens[start_token:end_token + 1],
        'task': 'paragraph'
    }


def load_paragraph_above(article_id, paragraph_id, sentence_id):
    """
    Finds the lists of tokens for a paragraph above a given sentence.

    :param article_id: int.
        The id of the Article of which we want the tokens for a paragraph.
    :param paragraph_id: int.
        The index of the paragraph for which we want the tokens.
    :param sentence_id: int.
        The index of the sentence for which we want the tokens above.
    :return: list(string).
        The tokens in paragraph paragraph_id.
    """
    try:
        article = Article.objects.get(id=article_id)
        tokens = article.tokens['tokens']
        paragraph_ends = article.paragraphs['paragraphs']
        sentence_ends = article.sentences['sentences']
    except ObjectDoesNotExist:
        return None

    if paragraph_id == 0:
        start_sentence = 0
    else:
        start_sentence = paragraph_ends[paragraph_id - 1] + 1
    end_sentence = sentence_id - 1
    if start_sentence == 0:
        start_token = 0
    else:
        start_token = sentence_ends[start_sentence - 1] + 1
    end_token = sentence_ends[end_sentence]
    return {
        'data': tokens[start_token:end_token + 1],
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
    return Article.objects.filter(label_counts__min_label_counts__lt=MIN_USER_LABELS)\
               .order_by('confidence__min_confidence')[:n]


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
    :return: (Article, int, list(int)).
        The article_id, paragraph_index and sentence_indices of the labelling task
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
            if min_conf >= CONFIDENCE_THRESHOLD\
                    and label_counts[prev_par_end + 1] < COUNT_THRESHOLD\
                    and (prev_par_end + 1) not in annotated_sentences:
                return article, i, []

            # For all sentences in the paragraph, check if they can be annotated by the user
            for j in range(prev_par_end + 1, p + 1):
                if label_counts[j] < COUNT_THRESHOLD and j not in annotated_sentences:
                    if j == 0:
                        sent_start = 0
                    else:
                        sent_start = sentence_ends[j - 1] + 1
                    sent_end = sentence_ends[j]
                    # List of sentence indices to label
                    labelling_task = [j]
                    # Checks that the sentence is not inside quotes
                    if article.in_quotes['in_quotes'][sent_start] == 1:
                        first_sent = quote_start_sentence(sentence_ends, article.in_quotes['in_quotes'], sent_start)
                        labelling_task = list(range(first_sent, j + 1))
                    if article.in_quotes['in_quotes'][sent_end] == 1:
                        last_sent = quote_end_sentence(sentence_ends, article.in_quotes['in_quotes'], sent_end)
                        labelling_task = list(range(labelling_task[0], last_sent + 1))
                    return article, i, labelling_task
            prev_par_end = p
    return None, [], []