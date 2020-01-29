from django.core.exceptions import ObjectDoesNotExist

from backend.frontend_parsing.postgre_to_frontend import form_paragraph_json, form_sentence_json
from backend.helpers import quote_end_sentence, is_sentence_labelled
from backend.models import Article, UserLabel
from backend.xml_parsing.xml_to_postgre import process_article


""" File containing all methods used for database management """


""" The minumum amount of user labels required for a sentence to be labeled. """
MIN_USER_LABELS = 4

""" The number of articles in which to check for sentences to label. """
ARTICLE_LOADS = 10

""" The minimum number of users needed for a sentence to be considered labelled. """
COUNT_THRESHOLD = 4

""" The minimum consensus required for a sentence to be considered labelled. """
CONSENSUS_THRESHOLD = 4

""" The minimum confidence required for an a full paragraph to be labeled at once. """
CONFIDENCE_THRESHOLD = 75

""" If only a single label is needed for each sentence. """
ADMIN_TAGGER = True


def add_user_label_to_db(user_id, article_id, sentence_index, labels, author_index, admin):
    """
    Adds a new user label to the database for a given user annotation.

    :param user_id: int.
        The users session id
    :param article_id: int.
        The key of the article that was annotated
    :param sentence_index: int.
        The index of the sentence that was labelled in the article
    :param labels: list(int).
        The labels the user created for the sentence
    :param author_index: list(int).
        The indices of the tokens that are authors for this sentence
    :param admin: bool.
        If the user is an admin.
    :return: UserLabel.
        The UserLabel created
    """
    # Get the article to which these labels belong
    try:
        article = Article.objects.get(id=article_id)
    except ObjectDoesNotExist:
        return None

    label_counts = article.label_counts['label_counts']
    # Increase the label count for the given tokens in the Article database
    label_counts[sentence_index] += 1
    article.label_counts = {
            'label_counts': label_counts,
            'min_label_counts': min(label_counts)
        }
    article.save()

    return UserLabel.objects.create(
            article=article,
            session_id=user_id,
            labels={'labels': labels},
            sentence_index=sentence_index,
            author_index={'author_index': author_index},
            admin_label=admin,
    )


def add_article_to_db(path, nlp, admin_article=False):
    """
    Loads an article stored as an XML file, and adds it to the database after having processed it.

    :param path: string.
        The URL of the stored XML file
    :param nlp: spaCy.Language.
        The language model used to tokenize the text.
    :param admin_article: boolean.
        Can this article only be seen by admins.
    :return: Article.
        The article created
    """
    # Loading an xml file as a string
    with open(path, 'r') as file:
        article_text = file.read()

    # Process the file
    data = process_article(article_text, nlp)
    label_counts = len(data['s']) * [0]
    label_overlap = len(data['s']) * [0]
    confidence = len(data['s']) * [0]
    return Article.objects.create(
        name=data['name'],
        text=article_text,
        people={'people': data['people']},
        tokens={'tokens': data['tokens']},
        paragraphs={'paragraphs': data['p']},
        sentences={'sentences': data['s']},
        label_counts={
            'label_counts': label_counts,
            'min_label_counts': 0
        },
        label_overlap={'label_overlap': label_overlap},
        in_quotes={'in_quotes': data['in_quotes']},
        confidence={
            'confidence': confidence,
            'min_confidence': 0,
        },
        admin_article=admin_article,
    )


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
    return Article.objects \
                .filter(label_counts__min_label_counts__lt=MIN_USER_LABELS) \
                .order_by('confidence__min_confidence', 'id')[:n]


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
                if not is_sentence_labelled(article, j, COUNT_THRESHOLD, CONSENSUS_THRESHOLD) and \
                        j not in annotated_sentences:
                    # List of sentence indices to label
                    labelling_task = [j]
                    # Checks that the sentence's last token is inside quotes, in which case the next sentence would
                    # also need to be returned
                    sent_end = sentence_ends[j]
                    if article.in_quotes['in_quotes'][sent_end] == 1:
                        last_sent = quote_end_sentence(sentence_ends, article.in_quotes['in_quotes'], sent_end)
                        labelling_task = list(range(labelling_task[0], last_sent + 1))
                    return form_sentence_json(article, labelling_task)
            prev_par_end = p
    return None


def set_admin_tagger(value):
    """
    Sets the value of the ADMIN_TAGGER constant

    :param value: Boolean.
        The value that ADMIN_TAGGER needs to be set to.
    """
    global ADMIN_TAGGER
    ADMIN_TAGGER = value


def get_admin_tagger():
    """
    :return: Boolean.
        The value of the ADMIN_TAGGER constant
    """
    global ADMIN_TAGGER
    return ADMIN_TAGGER
