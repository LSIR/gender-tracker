import xml.etree.ElementTree as ET

from backend.xml_parsing.named_entity_linking import extract_person_mentions

""" File containing all methods to parse XML files into representations that can be stored in the database. """


""" Quote characters that need to be unified to a single quote character. """
QUOTES = ["«", "»", "“", "”", "„", "‹", "›", "‟", "〝", "〞"]


def normalize_quotes(text, default_quote='"', quotes=None):
    """
    Normalizes all quote chars in a text by a default quote char.

    :param text: string.
        The string in which to normalize quotes.
    :param default_quote: char.
        The char to use for all quote chars in the text
    :param quotes: list(char).
        All characters that need to be replaced by default_quote
    :return: string.
        The normalized text
    """
    if quotes is None:
        quotes = QUOTES
    for q in quotes:
        text = text.replace(q, default_quote)
    return text


def get_element_text(el):
    """
    Given an element, extracts and sanitizes all text inside it. Removes all '\n' chars,
    and normalizes the quotes in it.

    :param el: ET.Element.
        The element from which to extract all text
    :return: string.
        The extracted text
    """
    # Text as list of strings
    ls = list(el.itertext())
    # Clean text
    text = ''.join(ls).replace('\n', '')
    text = ' '.join(text.split())
    return normalize_quotes(text)


def extract_paragraphs(root):
    """
    Parses the text contained in all paragraph tags of an article.

    :param root: ET.Element.
        The root element of the parsed XML article
    :return: list(spaCy.Doc).
        The list of paragraphs, processed as docs
    """
    elements = root.findall('p')
    return [get_element_text(el) for el in elements]


def extract_people(doc, start_index):
    """
    Given a paragraph and it's first tokens index, finds all the PER Named Entites in the
    paragraph.

    :param doc: spaCy.Doc.
        The doc representation of a paragraph
    :param start_index: int.
        The index of the first token in this paragraph for the whole article
    :return: list((int, int)).
        The list of all (start_token_index, end_token_index) pairs of PER NEs in the paragraph.
    """
    people = []
    for ent in doc.ents:
        if ent.label_ == 'PER':
            people.append((ent.start + start_index, ent.end + start_index))
    return people


def parse_text(article_text, nlp):
    """
    Parses an xml string into a spaCy doc for the full text.

    :param article_text: string.
        The article in XML format stored as a string
    :param nlp:
        spaCy.Language The language model used to tokenize the text
    :return: spaCy.Doc
        The parsed article text.
    """
    root = ET.fromstring(article_text)
    full_text = '\n'.join(extract_paragraphs(root))
    return nlp(full_text)


def process_article(article_text, nlp):
    """
    Processes an article stored as an XML file, and returns all the information necessary
    to store the article in the database.

    :param article_text: string.
        The article in XML format stored as a string
    :param nlp:
        spaCy.Language The language model used to tokenize the text
    :return: dictionary. (list(spaCy.Tokens), list(int), list(int), list((int, int)), list(int))
        'tokens': list(spaCy.Tokens). A list of all the tokens in the article
        'p': list(int). A list of the indices of sentences that are the last sentence of a paragraph.
        's': list(int). A list of the indices of tokens that are the last token of a sentence.
        'people': list(tuple). The first and last token of all Person Named Entities in the article.
        'in_quotes': list(int). For each token, 1 if it's in between quotes, 0 if it's note.
    """
    root = ET.fromstring(article_text)
    # Tries to extract the article title
    title_elements = list(root.findall('titre'))
    if len(title_elements) > 0:
        article_name = get_element_text(title_elements[0])
    else:
        article_name = 'No article title'

    # Extracts the article as a list of paragraphs
    paragraphs = extract_paragraphs(root)
    paragraphs = [nlp(p) for p in paragraphs]

    # The full text as a list of tokens
    article_tokens = []
    # A list of indices of sentences at which paragraphs end
    paragraph_indices = []
    # A list of indices of tokens at which sentences end
    sentence_indices = []
    # A list of all quotation mark indices in the article
    in_quote = 0
    in_quotes = []

    # The token index at which the previous sentence ended
    prev_sent_index = -1
    # The sentence index at which the previous paragraph ended
    prev_par_index = -1
    for p in paragraphs:
        for s in p.sents:
            for token in s:
                in_quotes.append(in_quote)
                if '"' in token.text and in_quote == 0:
                    in_quote = 1
                elif '"' in token.text:
                    in_quote = 0
                    in_quotes[-1] = 0
                article_tokens.append(token.text_with_ws)
            prev_sent_index += len(s)
            sentence_indices.append(prev_sent_index)
            prev_par_index += 1
        paragraph_indices.append(prev_par_index)

    people, mentions_found = extract_person_mentions(paragraphs)

    return {
        'name': article_name,
        'tokens': article_tokens,
        'p': paragraph_indices,
        's': sentence_indices,
        'people': people,
        'mentions': mentions_found,
        'in_quotes': in_quotes,
    }
