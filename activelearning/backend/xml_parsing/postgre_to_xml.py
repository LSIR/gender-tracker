from backend.helpers import is_article_labelled
from backend.models import Article
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
    for index, author in enumerate(resolve_overlapping_people(authors)):
        start_token = author[0]
        end_token = author[-1]
        tokens[start_token] = f'<author a={index}>' + tokens[start_token]
        tokens[end_token] = tokens[end_token] + f'</author>'
        authors_ids[f'{start_token}'] = index

    last_label = 0
    token_index = 0
    tagged_tokens = []
    for sentence_index in range(len(labels)):
        user_labels = labels[sentence_index]
        for label in user_labels:
            if label == 1 and last_label == 0:
                quote_author = authors_ids[authors[sentence_index][0]]
                tagged_tokens.append(f'<RS a={quote_author}>' + tokens[token_index])
                last_label = 1
            elif label == 0 and last_label == 1:
                tagged_tokens.append(tokens[token_index] + '</RS>')
                last_label = 0
            else:
                tagged_tokens.append(tokens[token_index])
            token_index += 1
    return tagged_tokens


def database_to_xml(output_path, min_users, min_consensus):
    """
    Extracts an annotated XML file for all articles that contain enough labels for each sentence.

    :param output_path: string.
        The path to an empty directory where the XML files need to be stored.
    :param min_users: int.

    :param min_consensus: float.

    :return: None.
    """
    articles = Article.objects.all()
    article_index = 0
    for article in articles:
        print(article.id)
        data = is_article_labelled(article, min_users, min_consensus)
        print(data is None)
        if data is not None:
            labels, authors = data
            text = '<article>'
            if article.name != 'No article title':
                text += f'<title>{article.name}</title>'
            tokens = add_tags_to_tokens(article.tokens['tokens'], labels, authors)
            p_start = 0
            for p_end in article.paragraphs['paragraphs']:
                text += '<p>' + ''.join(tokens[p_start:p_end+1]) + '</p>'
                p_start = p_end + 1
            text += '</article>'
            with open(f'{output_path}/article{article_index:04d}.xml', 'w') as f:
                f.write(text)
            article_index += 1
