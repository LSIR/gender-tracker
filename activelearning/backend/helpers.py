import xml.etree.ElementTree as ET
from backend.models import Article, UserLabel

##############################################################################################
# Constants
##############################################################################################

QUOTES = ["«", "»", "“", "”", "„", "‹", "›", "‟", "〝", "〞"]

##############################################################################################
# Loading and parsing articles
##############################################################################################


def load_article(article_path):
    """
    :return: an article whose quotes we want to label.
    Right now: loads the only xml-formatted article I have, and returns it as an ElementTree.
    Future: Probably load a random article (or a carefully selected one), parse it and return
    it as an ElementTree. How we choose each article to parse is the important part.
    """
    return ET.parse(article_path)


def parse_xml(xml_file):
    """
    :param xml_file: the ElementTree we want to parse into a JSON object
    :return: the ElementTree as a JSON object. 
    """
    root = xml_file.getroot()
    full_text = get_element_text(root)
    returned_text = full_text[:45] +  ' ...'
    split_words = returned_text.split(' ')
    return {'sentence': split_words}


##############################################################################################
# Save to Database
##############################################################################################


# Replace all formats of quotation marks by the quotation mark <">
def normalize_quotes(text, default_quote='"', quotes=QUOTES):
    """
    Normalizes all quote chars in a text by a default quote char.

    :param text: string The string in which to normalize quotes.
    :param default_quote: char The char to use for all quote chars in the text
    :param quotes: list(char) All characters that need to be replaced by default_quote
    :return: The normalized text
    """
    for q in QUOTES:
        text = text.replace(q, default_quote)
    return text


def get_element_text(el):
    """
    Given an element, extracts and sanitizes all text inside it. Removes all '\n' chars,
    and normalizes the quotes in it.

    :param el: ET.Element The element from which to extract all text
    :return: The extracted text 
    """
    # Text as list of strings
    ls = list(el.itertext())
    # Concatenate
    text = ''.join(ls)
    # Clean text
    text = ''.join(ls).replace('\n', '')
    text = ' '.join(text.split())
    return normalize_quotes(text)


def extract_paragraphs(root):
    """
    Parses the text contained in all paragraph tags of an article.

    :param root: ET.Element The root element of the parsed XML article
    :return: list(spacy.Doc) The list of paragraphs, processed as docs 
    """
    elements = root.findall('p')
    return [get_element_text(el) for el in elements]


def extract_people(doc, start_index):
    """
    Given a paragraph and it's first tokens index, finds all the PER Named Entites in the
    paragraph.

    :param doc: spacy.Doc The doc representation of a paragraph
    :param start_index: int The index of the first token in this paragraph for the whole article
    :return: list(int, int) The list of all (start_token_index, end_token_index) pairs of PER NEs 
        in the paragraph.
    """
    people = []
    for ent in doc.ents:
        if ent.label_ == 'PER':
            people.append((ent.start + start_index, ent.end + start_index))
    return people


def process_article(article_text, nlp):
    """
    Processes an article stored as an XML file, and returns all the information necessary 
    to store the article in the database.

    :param article_text: string The article in XML format stored as a string
    :param nlp: spacy.Language The language model used to tokenize the text
    :return: (list(spacy.Tokens), list(int), list(int), list((int, int)), list(int))
        All the tokens in the article,
        the indices of all tokens starting a paragraph, the indices of all tokens starting a sentence, all people
        found as Named Entities, boolean values representing if each token is in between quotes.
    """
    root = ET.fromstring(article_text)
    # Extracts the article as a list of paragraphs
    paragraphs = extract_paragraphs(root)
    paragraphs = [nlp(p) for p in paragraphs]

    # The full text as a list of tokens
    article_tokens = []
    # A list of indices of tokens at which paragraphs begin
    paragraph_indices = []
    # A list of indices of tokens at which sentences begin
    sentence_indices = []
    # A list of all PER named entities in the article, stored
    # as (start_token_index, end_token_index)
    people_indices = []
    # A list of all quotation mark indices in the article
    in_quotes_tagger = 0
    in_quotes = []
    
    # The index at which the previous sentence ended
    prev_index = 0
    for p in paragraphs:
        people_indices += extract_people(p, prev_index)
        paragraph_indices.append(prev_index)
        for s in p.sents:
            sentence_indices.append(prev_index)
            for token in s:
                if token.text == '"' and in_quotes_tagger == 0:
                    in_quotes_tagger = 1
                elif token.text == '"':
                    in_quotes_tagger = 0
                in_quotes.append(in_quotes_tagger)
                article_tokens.append(token.text)
            prev_index += len(s)
    
    return article_tokens, paragraph_indices, sentence_indices, people_indices, in_quotes


def add_article_to_db(url, nlp):
    """
    Loads an article stored as an XML file, and adds it to the database
    afterhaving processed it.

    :param url: string The URL of the stored XML file
    :param nlp: spacy.Language The language model used to tokenize the text
    :return: Article The article created
    """
    # Loading an xml file as a string
    with open(url, 'r') as file:
        article_text = file.read()
    
    # Process the file
    article_tokens, p_indices, s_indices, people_indices, in_quotes = process_article(article_text, nlp)
    label_counts = len(article_tokens) * [0]
    confidence = len(s_indices) * [0]
    return Article.objects.create(
        text=article_text,
        authors={'authors': people_indices},
        tokens={'tokens': article_tokens},
        paragraphs={'paragraphs': p_indices},
        sentences={'sentences': s_indices},
        label_counts={'label_counts': label_counts},
        in_quotes={'in_quotes': in_quotes},
        confidence={
            'confidence': confidence,
            'min_confidence': 0,
        }
    )


def add_user_labels_to_db(article_id, session_id, labels, sentence_index, author_index):
    """
    Adds a new set of user labels to the database for a given sentence.

    :param article_id: int The key of the article that was annotated
    :param session_id: int The users session id
    :param labels: list(int) The labels the user created
    :param sentence_index: int The index of the token at which this sentence starts
    :param author_index: list(int) The indices of the tokens that are authors for this sentence
    :return: UserLabel The UserLabel created
    """
    # Get the article to which these labels belong
    article = Article.objects.get(id=article_id)

    # Increase the label count for the given tokens in the Article database
    label_counts = article.label_counts['label_counts']
    sentence_starts = article.sentences['sentences']
    start_token = sentence_starts[sentence_index]
    end_token = sentence_starts[sentence_index + 1]
    for i in range(start_token, end_token):
        label_counts[i] += 1
    article.label_counts = {'label_counts': label_counts}
    article.save()

    # Create the user labels and return them
    return UserLabel.objects.create(
        article=article,
        session_id=session_id,
        labels={'labels': labels},
        sentence_index=sentence_index,
        author_index={'author_index': author_index}
    )


##############################################################################################
# Import from Database
##############################################################################################


def load_hardest_articles(n):
    """
    Loads the hardest articles to classify in the database, in terms of the confidence in the
    answers.

    :param n: int The number of articles to load from the database
    :return: list(Article) The n hardest articles to classify.
    """
    return Article.objects.all().order_by('confidence__min_confidence')[:n]


##############################################################################################
# User Requests
##############################################################################################