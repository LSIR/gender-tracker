

""" Contains methods for the baseline models for quote extraction and attribution. """


def find_longest_quote(in_quotes):
    """
    Finds the longest continuous sublist of ones in the list.

    :param in_quotes: list(int)
        The list of boolean (in {0, 1}) values indicating if each token is in a quote or not.
    :return: int, int
        The length of the longest sublist and the index of its first element
    """
    longest_sublist = 0
    start = 0
    sublist = None
    sublist_start = 0
    for index, token_in_quote in enumerate(in_quotes):
        if token_in_quote == 1:
            if sublist is None:
                sublist = 1
                sublist_start = index
            else:
                sublist += 1
        else:
            if sublist is not None:
                if sublist > longest_sublist:
                    longest_sublist = sublist
                    start = sublist_start
                sublist = None
    if sublist is not None:
        longest_sublist = max(sublist, longest_sublist)
        start = sublist_start

    return longest_sublist, start


def baseline_quote_detection(sent_span, in_quotes):
    """
    Rule-based model to determine if a sentence contains reported speech or not. Rule:

        A sentence is determined to contain reported speech if and only if it contains a piece of text of at least 3
        tokens between quotes, where all tokens between quotes aren't capitalized.

    :param sent_span: spaCy.Span
        The span of the sentence.
    :param in_quotes: list(int)
        Whether each token in each sentence is between quotes or not.
    :return: int
        Returns 0 if the model predicts that the sentence doesn't contain a quote, and 1 if it does.
    """
    # The longest substring between quotes is at least 3 tokens long
    longest_sublist, start = find_longest_quote(in_quotes)

    if longest_sublist >= 3:
        # Non-proper noun words are not all capitalized
        end = start + longest_sublist
        b = [word.shape_[0] == 'X' for word in sent_span[start:end + 1] if not (word.pos_ == "PUNCT" or
                                                                                word.ent_type != 0)]
        return int(False in b)
    return 0


def extract_cue_verb(sentence, cue_verbs):
    """
    Finds the first cue verb in the sentence, if there is one.

    :param sentence: spaCy.Span
        The span of the sentence.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return: spacy.Token
        None if the sentence contains no cue verb, and otherwise the token of the cue verb
    """
    for token in sentence:
        if token.lemma_ in cue_verbs:
            return token
    return None


def extract_quotee(sentence, token):
    """
    Given a sentence and a token in it which is a named entity, finds all other tokens that are a part of the same
    named entity.

    :param sentence: spaCy.Span
        The span of the sentence.
    :param token: spacy.Token
        The token that's a part of the named entity.
    :return: list(int)
        The indices of the tokens in the named entity in the sentence.
    """
    # Find the first token in the named entity
    index = token.i - sentence.start
    while index >= 0 and sentence[index].ent_iob == 1:
        index -= 1

    # Add the first token in the named entity
    ne_tokens = [index]
    index += 1
    # Add all tokens in the named entity
    while index < len(sentence) and sentence[index].ent_iob == 1:
        ne_tokens.append(index)
        index += 1

    return ne_tokens


def absolute_indices(relative_indices, sentence_start):
    """
    Finds the absolute position of the tokens from their position in a sentence.

    :param relative_indices: list(int)
        The relative positions.
    :param sentence_start: int
        The index of the first token in the sentence.
    :return: list(int)
        The absolute positions.
    """


def baseline_quote_attribution(all_sentences, sentence_index, sentence_starts, in_quotes, cue_verbs):
    """
    Baseline quote attribution model. This model selects a named entity for the quote in the following order:

        1. If the sentence containing the quote contains a cue verb which has a named entity as a child, return that
        named entity.

        2. If the sentence containing the quote contains a named entity that isn't between quotes, return that named
        entity.

        3. Return the first named entity above the sentence containing the quote, if there is one.

        4. Return the first named entity below the sentence containing the quote, if there is one.

        5. Return that there is no named entity that is the author of the reported speech.

    :param all_sentences: list(spacy.Span)
        All sentences in the article.
    :param sentence_index: int
        The index of the sentence in the article.
    :param sentence_starts: list(int)
        The index of the token at which each sentence starts.
    :param in_quotes: list(int)
        Whether each token in each sentence is between quotes or not.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return: list(int)
        The indices of the named entity in the article that is predicted to be the author of the quote. If there is
        none, returns an empty list.
    """
    sentence = all_sentences[sentence_index]
    s_in_quotes = in_quotes[sentence_index]

    # If the sentence contains a cue verb with a named entity as a dependent, return the named entity.
    cv = extract_cue_verb(sentence, cue_verbs)
    if cv is not None:
        for child in cv.children:
            if child.ent_type_ == "PER":
                return absolute_indices(extract_quotee(sentence, child), sentence_starts[sentence_index])

    # If the sentence contains a named entity that isn't between quotes, return that named entity
    for index, token in enumerate(sentence):
        if token.ent_type_ == "PER" and s_in_quotes[index] == 0:
            return absolute_indices(extract_quotee(sentence, token), sentence_starts[sentence_index])

    # Return the named entity above the sentence that is closest to it
    index = sentence_index - 1
    while index >= 0:
        for i, token in enumerate(all_sentences[index]):
            if token.ent_type_ == "PER":
                return absolute_indices(extract_quotee(all_sentences[index], token), sentence_starts[index])
        index -= 1

    # Return the first named entity after the quote
    index = sentence_index + 1
    while index < len(all_sentences):
        for i, token in enumerate(all_sentences[index]):
            if token.ent_type_ == "PER":
                return absolute_indices(extract_quotee(all_sentences[index], token), sentence_starts[index])
        index += 1

    # The sentence has no named entity as an author
    return []