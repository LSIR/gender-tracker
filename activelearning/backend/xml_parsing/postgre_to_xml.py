from backend.xml_parsing.helpers import resolve_overlapping_people


""" File containing all methods to transforms entries from the PostgreSQL database to XML files. """


def add_tags_to_tokens(tokens, labels, authors):
    """
    Adds XML tags to sentences containing quotes.

    :param tokens: list(string).
        The list of tokens in the article.
    :param labels: list(list(int)).
        The list of user labels for each sentence.
    :param authors: list(list(int)).
        The list of author indices for each sentence.
    :return: list(string).
        The list of tokens with tags appended to each token that requires one.
    """
    authors_ids = {}
    author_index = 0
    authors = resolve_overlapping_people(authors)
    for index, author_tokens in enumerate(authors):
        if len(author_tokens) > 0:
            start_token = author_tokens[0]
            end_token = author_tokens[-1]
            if f'{start_token}' not in authors_ids:
                tokens[start_token] = f'<author a="{author_index}">' + tokens[start_token]
                tokens[end_token] = tokens[end_token] + f'</author>'
                authors_ids[f'{start_token}'] = author_index
                author_index += 1

    last_label = 0
    token_index = 0
    tagged_tokens = []
    for sentence_index in range(len(labels)):
        user_labels = labels[sentence_index]
        for label in user_labels:
            if label == 1 and last_label == 0:
                author_tokens = authors[sentence_index]
                author_id = authors_ids[f'{author_tokens[0]}']
                tagged_tokens.append(f'<RS a="{author_id}">' + tokens[token_index])
                last_label = 1
            elif label == 0 and last_label == 1:
                tagged_tokens[-1] = tagged_tokens[-1] + '</RS>'
                tagged_tokens.append(tokens[token_index])
                last_label = 0
            else:
                tagged_tokens.append(tokens[token_index])
            token_index += 1
    if last_label == 1:
        tagged_tokens[-1] = tagged_tokens[-1] + '</RS>'
    return tagged_tokens


def database_to_xml(article, labels, authors):
    """
    Given an article, as well as the consensus (the most common label amongst user labels) labels and quote
    authors for all sentences, computes the string for an xml file for the annotated article.

    :param article: Article.
        An instance of the article database.
    :param labels: list(list(int)).
        The list of user labels for each sentence.
    :param authors:
        The list of authors for each sentence.
    :return: String.
        A string with the content of the XML file.
        Returns None if the article doesn't have enough user labels.
    """
    text = '<?xml version="1.0"?>\n<article>\n'
    if article.name != 'No article title':
        text += f'\t<titre>{article.name}</titre>\n'
    tokens = add_tags_to_tokens(article.tokens['tokens'], labels, authors)
    first_token_of_paragraph = 0
    for p_end in article.paragraphs['paragraphs']:
        last_sentence_of_paragraph = p_end
        last_token_of_paragraph = article.sentences['sentences'][last_sentence_of_paragraph]
        text += '\t<p>' + ''.join(tokens[first_token_of_paragraph:last_token_of_paragraph+1]) + '</p>\n'
        first_token_of_paragraph = last_token_of_paragraph + 1

    text += '</article>'
    return text
