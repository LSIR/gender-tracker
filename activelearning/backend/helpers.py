import xml.etree.ElementTree as ET
from backend.models import Article, UserLabel

##############################################################################################
# Constants
##############################################################################################

QUOTES = ["«", "»", "“", "”", "„", "‹", "›", "‟", "〝", "〞"]

COUNT_THRESHOLD = 3

ARTICLE_LOADS = 5

CONFIDENCE_THRESHOLD = 80

MIN_USER_LABELS = 4

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
    returned_text = full_text[:45] + ' ...'
    split_words = returned_text.split(' ')
    return {'sentence': split_words}


def form_sentence_json(article, paragraph_id, sentence_id):
    """
    Given an article and some sentence indices in the article, forms a dict containing the key-value pairs article_id
    (int), a paragraph_id (int), a sentence_id ([int]), data (list[string]) and  task ('sentence').

    If a sentence needs to be labelled, sentence_id is a list of a least one integer, and data is a list of individual
    tokens (words).

    :param article: Article The article that needs to be labelled
    :param paragraph_id: int The index of the paragraph that contains the sentences that need to be labelled
    :param sentence_id: list(int) The indices of the sentences in the Article that need to be labelled
    :return: dict A dict containing article_id, paragraph_id, sentence_id, data and task keys
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

    :param article: Article The article that needs to be labelled
    :param paragraph_id: int The index of the paragraph in the Article that needs to be labelled
    :return: dict A dict containing article_id, paragraph_id, sentence_id, data and task keys
    """
    tokens = article.tokens['tokens']
    if paragraph_id == 0:
        start_token = 0
    else:
        start_token = article.paragraphs['paragraphs'][paragraph_id - 1] + 1
    end_token = article.paragraphs['paragraphs'][paragraph_id]
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

    :param article_id: int. The id of the Article of which we want the tokens for a paragraph.
    :param paragraph_id: int. The index of the paragraph for which we want the tokens.
    :param sentence_id: int. The index of the sentence for which we want the tokens above.
    :return: list(string). The tokens in paragraph paragraph_id.
    """
    article = Article.objects.get(id=article_id)
    tokens = article.tokens['tokens']
    paragraph_ends = article.paragraphs['paragraphs']
    sentence_ends = article.sentences['sentences']
    if paragraph_id == 0:
        start_sentence = 0
    else:
        start_sentence = paragraph_ends[paragraph_id - 1] + 1
    end_sentence = paragraph_ends[paragraph_id]
    if start_sentence == 0:
        start_token = 0
    else:
        start_token = sentence_ends[start_sentence - 1] + 1
    end_token = sentence_ends[end_sentence]
    return {
        'data': tokens[start_token:end_token + 1],
    }


##############################################################################################
# Save to Database
##############################################################################################


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
    # A list of indices of sentences at which paragraphs end
    paragraph_indices = []
    # A list of indices of tokens at which sentences end
    sentence_indices = []
    # A list of all PER named entities in the article, stored
    # as (start_token_index, end_token_index)
    people_indices = []
    # A list of all quotation mark indices in the article
    in_quote = 0
    in_quotes = []
    
    # The token index at which the previous sentence ended
    prev_sent_index = -1
    # The sentence index at which the previous paragraph ended
    prev_par_index = -1
    for p in paragraphs:
        people_indices += extract_people(p, prev_sent_index + 1)
        for s in p.sents:
            for token in s:
                in_quotes.append(in_quote)
                if token.text == '"' and in_quote == 0:
                    in_quote = 1
                elif token.text == '"':
                    in_quote = 0
                    in_quotes[-1] = 0
                article_tokens.append(token.text)
            prev_sent_index += len(s)
            sentence_indices.append(prev_sent_index)
            prev_par_index += 1
        paragraph_indices.append(prev_par_index)
    
    return article_tokens, paragraph_indices, sentence_indices, people_indices, in_quotes


def add_article_to_db(path, nlp):
    """
    Loads an article stored as an XML file, and adds it to the database after having processed it.

    :param path: string The URL of the stored XML file
    :param nlp: spacy. Language The language model used to tokenize the text
    :return: Article The article created
    """
    # Loading an xml file as a string
    with open(path, 'r') as file:
        article_text = file.read()
    
    # Process the file
    article_tokens, p_indices, s_indices, people_indices, in_quotes = process_article(article_text, nlp)
    label_counts = len(s_indices) * [0]
    confidence = len(s_indices) * [0]
    return Article.objects.create(
        text=article_text,
        authors={'authors': people_indices},
        tokens={'tokens': article_tokens},
        paragraphs={'paragraphs': p_indices},
        sentences={'sentences': s_indices},
        label_counts={
            'label_counts': label_counts,
            'min_label_counts': 0
        },
        in_quotes={'in_quotes': in_quotes},
        confidence={
            'confidence': confidence,
            'min_confidence': 0,
        }
    )


def add_user_labels_to_db(article_id, session_id, labels, sentence_index, author_index):
    """
    Adds a new set of user labels to the database for a given user annotation.

    :param article_id: int The key of the article that was annotated
    :param session_id: int The users session id
    :param labels: list(int) The labels the user created for the sentence
    :param sentence_index: int The index of the sentence that was labelled in the article
    :param author_index: list(int) The indices of the tokens that are authors for this sentence
    :return: UserLabel The UserLabel created
    """
    # Get the article to which these labels belong
    article = Article.objects.get(id=article_id)
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
    # Return only articles that don't have
    return Article.objects.filter(label_counts__min_label_counts__lt=MIN_USER_LABELS)\
               .order_by('confidence__min_confidence')[:n]


##############################################################################################
# Labelling tasks
##############################################################################################


def quote_start_sentence(sentence_ends, in_quote, token_index):
    """
    Given the index of the first token of a sentence, which is inside quotation marks, returns the index of the sentence
    where the quotation mark started.

    :param sentence_ends: list(int) The list of the last token of each sentence
    :param in_quote: list(int) The list of in_quote tokens
    :param token_index: int The index of the token in the quote
    :return: int The index of the sentence containing the first token in the quote
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

    :param sentence_ends: list(int) The list of the last token of each sentence
    :param in_quote: list(int) The list of in_quote tokens
    :param token_index: int The index of the last token in the sentence
    :return: int The index of the sentence containing the last token in the quote
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

    :param session_id: int The user's session id
    :return: (Article, int, list(int)) The article_id, paragraph_index and sentence_indices of the labelling task
    """
    session_labels = UserLabel.objects.filter(session_id=session_id)
    for article in load_hardest_articles(ARTICLE_LOADS):
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
    return None, [], []


def parse_user_tags(article_id, paragraph_index, sentence_indices, tags, authors):
    """
    Computes the indices of tokens that are authors and cleans the user tags to only contain words that are in the
    quotes, and not the tags for authors.

    :param article_id: int The id of the article where the user performed a labelling task
    :param paragraph_index: int The index of the paragraph in the article where the user performed a labelling task
    :param sentence_indices: list(int) The indices of the sentences where the user performed a labelling task, and an
                                empty list if the user labelled the whole article.
    :param tags: list(int) The user tags
    :return:
    """
    article = Article.objects.get(id=article_id)
    sentence_ends = article.sentences['sentences']
    # Find the tagged sentences if the whole paragraph is tagged.
    if len(sentence_indices) == 0:
        if paragraph_index == 0:
            p_start = 0
        else:
            p_start = article.paragraphs['paragraphs'][paragraph_index - 1] + 1
        p_end = article.paragraphs['paragraphs'][paragraph_index]
        sentence_indices = range(p_start, p_end + 1)

    # Find the index of the first token tagged
    if sentence_indices[0] == 0:
        sentence_start = 0
    else:
        sentence_start = sentence_ends[sentence_indices[0] - 1] + 1

    # Transform relative index to absolute index
    author_indices = []
    for index in authors:
        author_indices.append(sentence_start + index)

    # Split the tags into labels for each sentence
    sentence_labels = []
    first_tag_index = 0
    for index in sentence_indices:
        last_tag_index = first_tag_index + (sentence_ends[index] - sentence_start)
        sentence_labels.append(tags[first_tag_index:last_tag_index + 1])
        first_tag_index = last_tag_index + 1
        sentence_start = sentence_ends[index] + 1

    return sentence_labels, sentence_indices, author_indices

##############################################################################################
# Learning
##############################################################################################


def change_confidence(article_id, sentence_confidence):
    """
    Edits the Article database to reflect that the trained model has changed his confidence level that each sentence is
    or isn't reported speech.

    :param article_id: int The id of the article to edit
    :param sentence_confidence: list(int) The confidence (in [0, 100]) the trained model has for each sentence.
    :return: int. The minimum confidence this article has in a sentence, or -1 if the article couldn't be added to the
                    database.
    """
    article = Article.objects.get(id=article_id)
    old_conf = article.confidence['confidence']
    min_conf = min(sentence_confidence)
    if len(sentence_confidence) == len(old_conf) and min_conf >= 0 and max(sentence_confidence) <= 100:
        new_conf = {
            'confidence': sentence_confidence,
            'min_conf': min_conf,
        }
        article.confidence = new_conf
        article.save()
        return min_conf
    return -1
