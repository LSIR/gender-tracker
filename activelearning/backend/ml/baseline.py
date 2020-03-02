from spacy.matcher import Matcher


def is_quote(text):
    """


    :param text:
    :return:
    """
    # Quote at least 3 tokens long
    a = len(text) >= 3
    # Non-proper noun words are not all capitalized
    b = [word.shape_[0] == 'X' for word in text if not word.pos_ in ["PROPN", "PUNCT"]]
    return a and (False in b)


def extract_cue_verb(sentence, cue_verbs):
    """

    :param sentence:
    :param cue_verbs:
    :return:
    """
    for token in sentence:
        if token.lemma_ in cue_verbs:
            return token
    return None


def extract_quotee(token):
    """

    :param token:
    :return:
    """
    quotee = ""
    for t in token.subtree:
        quotee += t.text + t.whitespace_
    return quotee


def baseline_quote_detection(sentence, nlp):
    """

    :param sentence:
    :param nlp:
    :return:
    """
    matcher = Matcher(nlp.vocab, validate=True)
    # Add match ID "Quote"
    pattern = [{"TEXT": '"'}]
    matcher.add("Quote", None, pattern)

    # Find the quote matches
    matches = matcher(sentence)
    opening_quotes = []
    closing_quotes = []
    for match_id, start, end in matches:
        if len(opening_quotes) == len(closing_quotes):
            opening_quotes.append(start)
        else:
            closing_quotes.append(start + 1)

    quote_pos = zip(opening_quotes, closing_quotes)
    for (start, end) in quote_pos:
        quote = sentence[start:end]
        if is_quote(quote):
            return 1
    return 0


def baseline_quote_attribution(sentence_index, full_article, sentence_starts, in_quotes, cue_verbs):
    """


    :param sentence_index: int
    :param full_article: list(spaCy.Doc)
    :param sentence_starts: list(int)
    :param in_quotes:
    :param cue_verbs:
    :return: list(int)
        The indices of the tokens in the article that represent the quotee.
    """
    sentence = full_article[sentence_index]
    cv = extract_cue_verb(sentence, cue_verbs)
    # If the sentence contains a cue verb with a named entity as a dependent, return the named entity.
    if cv is not None:
        for child in cv.children:
            if child.pos_ == "PROPN":
                return extract_quotee(child)

    # If the sentence contains a named entity that isn't between quotes, return that named entity
    for index, token in enumerate(sentence):
        if token.pos_ == "PROPN" and in_quotes[index] == 0:
            return extract_quotee(token)

    # Return the named entity above the sentence that is closest to it
    index = sentence_index - 1
    while index >= 0:
        for i, token in enumerate(sentence):
            if token.pos_ == "PROPN":
                return extract_quotee(token)

    # Return the first named entity after the quote

    # The sentence has no named entity as an author
