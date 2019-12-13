from django.core.exceptions import ObjectDoesNotExist

from backend.models import Article, UserLabel
from backend.xml_parsing import process_article
from .helpers import paragraph_sentences
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
    if paragraph_index < 0 or len(article.paragraphs['paragraphs']) <= paragraph_index:
        return None

    if len(sentence_indices) > 0 and (sentence_indices[0] < 0 or
                                      sentence_indices[-1] > len(article.sentences['sentences'])):
        return None

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


def add_labels_to_database(user_id, article_id, paragraph_index, sentence_indices, tags, authors, admin):
    """
    Given the raw data the user generated (article id, paragraph, sentences tagged, labels, and authors for the quotes
    found), separates the labels into labels for individual sentences and adds them to the database.

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
    :param admin: bool.
        If the user that created the labels is an admin
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
        add_user_label_to_db(user_id, article_id, sentence_indices[i], sentence_labels[i], author_indices, admin)


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