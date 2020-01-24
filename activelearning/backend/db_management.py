from django.core.exceptions import ObjectDoesNotExist

from backend.models import Article, UserLabel
from backend.xml_parsing.xml_to_postgre import process_article


""" File containing all methods used for database management """


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