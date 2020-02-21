from django.core.exceptions import ObjectDoesNotExist

import numpy as np

import random

from backend.frontend_parsing.postgre_to_frontend import form_paragraph_json, form_sentence_json
from backend.helpers import quote_end_sentence, label_consensus, aggregate_label
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
CONSENSUS_THRESHOLD = 0.75

""" The minimum confidence required for an a full paragraph to be labeled at once. """
CONFIDENCE_THRESHOLD = 0.8


def add_user_label_to_db(user_id, article_id, sentence_index, labels, author_index, admin):
    """
    Adds a new user label to the database for a given user annotation. If this label is admin, sets the labeled value
    for this sentence in the corresponding article to 1. Otherwise, finds all other user labels for this sentence, and
    computes their consensus (the proportion that agree on a response), and if their consensus is above the threshold
    and there are enough user labels, sets the labeled value for this sentence in the corresponding article to 1.

    If the annotated labels is an empty list, it means that the user didn't know how to annotate the sentence correctly.

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

    labeled = article.labeled['labeled']

    if labels != []:
        # User knew how to annotate: recompute consensus to see if sentence is fully labeled.
        if admin:
            labeled[sentence_index] = 1
        else:
            other_userlabels = UserLabel.objects.filter(article=article, sentence_index=sentence_index)
            # Only keep valid user labels
            other_userlabels = other_userlabels.exclude(labels__labels=[])
            other_labels = [userlabel.labels['labels'] for userlabel in other_userlabels]
            other_authors = [userlabel.author_index['author_index'] for userlabel in other_userlabels]

            all_labels = other_labels + [labels]
            all_authors = other_authors + [author_index]

            _, _, consensus = label_consensus(all_labels, all_authors)
            labeled[sentence_index] = int(consensus >= CONSENSUS_THRESHOLD and len(all_labels) >= COUNT_THRESHOLD)

        fully_labeled = int(sum(labeled) == len(labeled))
        article.labeled = {
                'labeled': labeled,
                'fully_labeled': fully_labeled,
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


def add_article_to_db(path, nlp, source, admin_article=False):
    """
    Loads an article stored as an XML file, and adds it to the database after having processed it.

    :param path: string.
        The URL of the stored XML file
    :param nlp: spaCy.Language.
        The language model used to tokenize the text.
    :param source: string.
        The newspaper in which the article was published.
    :param admin_article: boolean.
        Can this article only be seen by admins.
    :return: Article.
        The article created
    """
    # Loading an xml file as a string
    with open(path, 'r') as file:
        article_text = file.read()

    article_text = article_text.replace('&', '&amp;')
    # Process the file
    data = process_article(article_text, nlp)
    labeled = len(data['s']) * [0]
    confidence = len(data['s']) * [0]
    return Article.objects.create(
        name=data['name'],
        text=article_text,
        people={'people': data['people']},
        tokens={'tokens': data['tokens']},
        paragraphs={'paragraphs': data['p']},
        sentences={'sentences': data['s']},
        labeled={
            'labeled': labeled,
            'fully_labeled': 0,
        },
        in_quotes={'in_quotes': data['in_quotes']},
        confidence={
            'confidence': confidence,
            'min_confidence': 0,
        },
        admin_article=admin_article,
        source=source,
    )


def load_hardest_articles(n=None):
    """
    Loads the hardest articles to classify in the database, in terms of the confidence in the
    answers.

    :param n: int.
        If None, all articles are returned.
        Otherwise, limited to n articles.
    :return: list(Article).
        The n hardest articles to classify.
    """
    unlabeled_articles = Article.objects.filter(labeled__fully_labeled=0)
    # Randomly select an article source, load all of its unlabeled articles
    r = random.random()
    if r < 1/3:
        filtered_by_source = unlabeled_articles.filter(source='Heidi.News')
    elif r > 2/3:
        filtered_by_source = unlabeled_articles.filter(source='Parisien')
    else:
        filtered_by_source = unlabeled_articles.filter(source='Republique')
    # If it has at least one unlabeled article, return those. Otherwise return from all sources.
    if len(filtered_by_source) > 0:
        unlabeled_articles = filtered_by_source
    if n is None:
        return unlabeled_articles.order_by('confidence__min_confidence', 'id')
    else:
        return unlabeled_articles.order_by('confidence__min_confidence', 'id')[:n]


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
        labeled = article.labeled['labeled']
        confidences = article.confidence['confidence']
        sentence_ends = article.sentences['sentences']
        prev_par_end = -1
        # p is the index of the last sentence in paragraph i
        for (i, p) in enumerate(article.paragraphs['paragraphs']):
            # Lowest confidence in the whole paragraph
            min_conf = min([conf for conf in confidences[prev_par_end + 1:p + 1]])

            # For high enough confidences, annotate the whole paragraph
            if min_conf >= CONFIDENCE_THRESHOLD \
                    and labeled[prev_par_end + 1] == 0 \
                    and (prev_par_end + 1) not in annotated_sentences:
                return form_paragraph_json(article, i)

            # For all sentences in the paragraph, check if they can be annotated by the user
            for j in range(prev_par_end + 1, p + 1):
                if not article.labeled['labeled'][j] == 1 and j not in annotated_sentences:
                    # List of sentence indices to label
                    labelling_task = [j]
                    # Checks that the sentence's last token is inside quotes, in which case the next sentence would
                    # also need to be returned
                    sent_end = sentence_ends[j]
                    if article.in_quotes['in_quotes'][sent_end] == 1:
                        last_sent = quote_end_sentence(sentence_ends, article.in_quotes['in_quotes'], sent_end)
                        labelling_task = list(range(labelling_task[0], min(last_sent + 1, len(sentence_ends))))
                    return form_sentence_json(article, labelling_task)
            prev_par_end = p
    return None


def load_sentence_labels(nlp):
    """
    Finds all fully labeled articles. Extracts all sentences from each article, as well as a label for each sentence: 0
    if it doesn't contain reported speech, and 1 if it does. Assigns sentences in newly labeled articles to either the
    training or test set. Each sentence is added to the test set with 10% probability.

    :param nlp: spaCy.Language
        The language model used to tokenize the text.
    :return: list(string), list(int), list(string), list(int)
        * the list of all training sentences
        * the list of all training labels
        * the list of all testing sentences
        * the list of all testing labels
    """
    articles = Article.objects.filter(labeled__fully_labeled=1)
    train_sentences = []
    train_labels = []
    train_in_quotes = []
    test_sentences = []
    test_labels = []
    test_in_quotes = []
    for article in articles:
        start = 0
        # Check if the article already has its sentences assigned to the test or training set.
        if 'test_set' not in article.labeled:
            article.labeled['test_set'] = [int(np.random.random() > 0.9) for _ in range(len(article.labeled['labeled']))]
        for sentence_index, end in enumerate(article.sentences['sentences']):
            # Extract sentence text
            tokens = article.tokens['tokens'][start:end + 1]
            in_quotes = article.in_quotes['in_quotes'][start:end + 1]
            sentence = nlp(''.join(tokens))
            # Compute consensus labels
            sentence_labels, sentence_authors, _ = aggregate_label(article, sentence_index)
            # Adds the data to the correct list
            if article.labeled['test_set'][sentence_index] == 0:
                train_sentences.append(sentence)
                train_labels.append(int(sum(sentence_labels) > 0))
                train_in_quotes.append(in_quotes)
            else:
                test_sentences.append(sentence)
                test_labels.append(int(sum(sentence_labels) > 0))
                test_in_quotes.append(in_quotes)
            start = end + 1

    return train_sentences, train_labels, train_in_quotes, test_sentences, test_labels, test_in_quotes


def load_unlabeled_sentences(nlp):
    """
    Finds all articles that aren't fully labeled, and extracts all sentences from each.

    :param nlp: spaCy.Language
        The language model used to tokenize the text.
    :return: list(backend.models.Article), list(list(string))
        * the list of all articles that aren't fully labeled.
        * the list of the list of sentences in each article.
    """
    articles = list(Article.objects.filter(labeled__fully_labeled=0))
    sentences = []
    in_quotes = []
    for article in articles:
        start = 0
        article_sentences = []
        for sentence_index, end in enumerate(article.sentences['sentences']):
            # Extract sentence text
            tokens = article.tokens['tokens'][start:end + 1]
            sentence = nlp(''.join(tokens))
            article_sentences.append(sentence)
            in_quotes.append(article.in_quotes['in_quotes'][start:end + 1])
            start = end + 1
        sentences.append(article_sentences)

    return articles, sentences, in_quotes
