from backend.helpers import paragraph_sentences


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


def clean_user_labels(sentence_ends, task_indices, first_sentence, last_sentence, labels, authors):
    """
    Given the raw data the user generated (article id, paragraph, sentences tagged, labels, and authors for the quotes
    found), separates the labels into labels for individual sentences and adds them to the database.

    :param sentence_ends: list(int).
        The index of the last token of every sentence in the article.
    :param task_indices: list(int).
        The indices of the sentences the user was tasked to label.
    :param first_sentence: list(int).
        The index of the first sentence which has tagged values. Different from the first index of sentence indices if
        the user loaded extra text.
    :param last_sentence: list(int).
        The index of the last sentence which has tagged values. Different from the first index of sentence indices if
        the user loaded extra text.
    :param labels: list(int).
        The labels the user created
    :param authors: list(int).
        The relative position of the author of the quote, if there is one.
    :return: list(dict).
        The list of user labels, with their sentence indices, to add to the database. The dict contains the fields:
            index: int. The index of the sentence with these labels.
            labels: list(int). The list of labels to add to the database.
            authors: list(int). A list containing the index of tokens that are authors for the quote.
    """
    # Check that tags contain only 0s and 1s, and if they contain 1s that they are continuous
    first_one_seen = False
    first_one_segment_seen = False
    for label in labels:
        # If labels not in {0, 1} ignore
        if label not in [0, 1]:
            return []
        # Two different quotes found
        if first_one_segment_seen and label == 1:
            return []
        if first_one_seen and label == 0:
            first_one_segment_seen = True
        if not first_one_seen and label == 1:
            first_one_seen = True

    # Find the first and last token of each sentence
    sentence_starts = [0] + [end + 1 for end in sentence_ends][:-1]
    sentence_edges = list(zip(sentence_starts, sentence_ends))
    sentence_edges = sentence_edges[first_sentence:last_sentence + 1]

    # Transform the relative author index to the index of the tokens with respect to the full article by adding the
    # index of the first token in the tags in the article.
    author_indices = []
    for index in authors:
        author_indices.append(sentence_edges[0][0] + index)

    # Split the tags into tags for each sentence
    split_labels = []
    total_length = 0
    for edges in sentence_edges:
        sentence_length = edges[1] - edges[0] + 1
        split_labels = split_labels + [labels[total_length:total_length + sentence_length]]
        total_length += sentence_length

    # Check that there are the correct number of labels for the text
    if total_length != len(labels):
        return []

    task_first_sentence = task_indices[0] - first_sentence
    task_last_sentence = task_indices[-1] - first_sentence

    # Labels for sentence before the task asked of the user
    before_task_labels = split_labels[:task_first_sentence]
    # Labels for sentence in the task asked of the user
    task_labels = split_labels[task_first_sentence:task_last_sentence + 1]
    # Labels for sentence after the task asked of the user
    after_task_labels = split_labels[task_last_sentence + 1:]

    # Boolean values indicating if each sentence is inside the quote, if there is one.
    task_contains_ones = [sum(tag) > 0 for tag in task_labels]

    # Labels to add to the database
    clean_labels = []

    # If the user didn't report any quotes in sentences that he was tasked to label, add labels for only those sentences
    # to the database, reporting that they aren't a part of a quote.
    if sum(task_contains_ones) == 0:
        for index, sentence_labels in enumerate(task_labels):
            sentence_index = index + task_indices[0]
            clean_labels.append({
                'index': sentence_index,
                'labels': sentence_labels,
                'authors': [],
            })
    # The user reports quotes in the sentences he was tasked to label
    else:
        # Add the sentence labels for the task
        for index, sentence_labels in enumerate(task_labels):
            sentence_index = index + task_indices[0]
            clean_labels.append({
                'index': sentence_index,
                'labels': sentence_labels,
                'authors': author_indices,
            })

        # If some sentences before the original task are also in the quote, add labels for them too.
        for index, sentence_labels in enumerate(before_task_labels):
            if sum(sentence_labels) > 0:
                sentence_index = index + first_sentence
                clean_labels.append({
                    'index': sentence_index,
                    'labels': sentence_labels,
                    'authors': author_indices,
                })

        # If some sentences after the original task are also in the quote, add labels for them too
        for index, sentence_labels in enumerate(after_task_labels):
            if sum(sentence_labels) > 0:
                sentence_index = (last_sentence - len(after_task_labels) + 1) + index
                clean_labels.append({
                    'index': sentence_index,
                    'labels': sentence_labels,
                    'authors': author_indices,
                })

    return clean_labels


