import numpy as np
from spacy.tokens import Span

"""
Contains all methods to extract features from sentences to determine if they contain a quote or not, as well as
methods to extract features to determine speaker extraction for quotes. 
"""

""" The number of features used to detect if a sentence contains reported speech. """
QUOTE_FEATURES = 9

""" The number of features used to detect if a named entity is the author of reported speech. """
SPEAKER_FEATURES = 7


def is_substring(person, name):
    """
    Determines if name is a substring of person.

    :param person: string
        The complete string.
    :param name: string
        The string for which we want to know if it's a substring of person.
    :return: boolean
        True iff name is a subtring of person
    """
    person_tokens = person.split(' ')
    name_tokens = name.split(' ')
    for i in range(len(person_tokens)):
        j = 0
        while (i + j) < len(person_tokens) and j < len(name_tokens) and person_tokens[i + j] == name_tokens[j]:
            j = j + 1
        if j == len(name_tokens):
            return True
    return False


def find_full_name(all_people, name):
    """
    Determines if name is simply another mention of someone in all_people, or if it's the first mention of someone.

    :param all_people: list(string)
        The full name of everyone already seen in the document.
    :param name: string
        The mention of some person.
    :return:
        The full name of the person of it's another mention, or name if it's the first mention.
    """
    for person in all_people:
        if is_substring(person, name):
            return person
    return name


def correct_hyphen_errors(article):
    """
    Corrects an error that spaCy makes (seperates names that contain a hyphen into two named entities).

    :param article: spaCy.Doc
        The article in which to correct the entities.
    :return: list(spaCy.Span)
        The corrected entities.
    """
    entities = article.ents
    corrected_ents = []
    prev_per_ent = None
    for ent in entities:
        if ent.label_ == 'PER':
            if (prev_per_ent is not None) and \
                    (prev_per_ent.end_char == ent.start_char - 1) and \
                    (article.text[prev_per_ent.end_char] == '-'):
                # Create a new NE for the name with the hyphen
                merged_ent = Span(article, prev_per_ent.start, ent.end, label="PER")
                # Remove the last entity and add the new one.
                corrected_ents[-1] = merged_ent
            else:
                corrected_ents.append(ent)
            prev_per_ent = ent
        else:
            corrected_ents.append(ent)
            prev_per_ent = None
    return corrected_ents


def extract_person_mentions(article):
    """
    Finds all mentions of people in the article, and groups them into the same entity.

    :param article: spaCy.Doc
        The article text in which to find speaker mentions.
    :return: set(string), list(spaCy.Span), list(string)
        * A set containing the names of all people in the article
        * A list of all mentions of people in the article
        * A list of the full names of all people mentioned

    """
    # Correct entity splits on hyphens
    article.ents = correct_hyphen_errors(article)
    # Extract all mentions of people
    person_mentions = [ent for ent in article.ents if ent.label_ == 'PER']
    # Sort from the longest name to the shortest
    person_mentions.sort(key=lambda x: -len(x.text.split(' ')))
    # The set of people mentioned in the article (their full name)
    people = set()
    # Each mention of a person in the text
    mentions = []
    # The full name for each mention
    full_names = []
    for mention in person_mentions:
        mentions.append(mention)
        if mention.text not in people:
            full_name = find_full_name(people, mention.text)
            full_names.append(full_name)
            if mention.text == full_name:
                people.add(mention.text)
        else:
            full_names.append(mention.text)

    return people, mentions, full_names


def extract_quote_features(sentence, cue_verbs, in_quotes):
    """
    Gets features for possible elements in the sentence that can hint to it having a quote:
        * The length of the sentence.
        * Whether it contains quotation marks.
        * If the sentence contains quotation marks:
            * The number of tokens between them.
            * TODO: What if there are multiple quotes in the sentence?
                * Have a fixed number of entries like "tokens between first, second, and third quotes" and most of the
                time second and third are empty?
        * Whether it contains a named entity that is a person.
        * Whether it contains a verb in the verb-cue list.
        * Presence of a parataxis.
        * Presence of multiple verbs.
        * TODO: Presence of a verb in between quotes
        * Is the whole sentence in between quotes
        * The proportion of tokens in the sentence that are between quotes

    :param sentence: spaCy.doc.
        The sentence to extract features from.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :param in_quotes: list(int).
        Whether each token in the sentence is between quotes or not
    :return: np.array
        The features extracted.
    """
    contains_quote = int('"' in sentence.text)

    def tokens_inside_quote():
        tokens_inside = 0
        start_mark_seen = False
        end_mark_seen = False
        for token in sentence:
            if not start_mark_seen and token.text == '"':
                start_mark_seen = True
            elif start_mark_seen and not end_mark_seen and token.text == '"':
                end_mark_seen = True
            elif start_mark_seen and not end_mark_seen:
                tokens_inside += 1
        return tokens_inside

    contains_named_entity = int(len(sentence.ents) > 0)

    def contains_cue_verb():
        for token in sentence:
            if token.lemma_ in cue_verbs:
                return 1
        return 0

    def contains_pronoun():
        for token in sentence:
            if token.pos_ == 'PRON':
                return 1
        return 0

    def contains_parataxis():
        for token in sentence:
            if token.dep_ == 'parataxis':
                return 1
        return 0

    sentence_inside_quotes = int(len(in_quotes) == sum(in_quotes))
    inside_quote_proportion = sum(in_quotes)/len(in_quotes)

    return np.array([
        len(sentence),
        contains_quote,
        tokens_inside_quote(),
        contains_named_entity,
        contains_cue_verb(),
        contains_pronoun(),
        contains_parataxis(),
        sentence_inside_quotes,
        inside_quote_proportion
    ])


def extract_single_speaker_features(article, article_doc, quote_index, other_quotes, speaker, cue_verbs):
    """
    Gets the features for speaker attribution for a single speaker, in the one vs one case. The following features are
    taken, for a quote q and a speaker s where q.sent is the index of the sentence containing the quote, s.start is the
    index of the first token of the speaker s, s.end of the last, and s.sent is the index:

        * the distance between q and s: q.sent - s.sent
            * The value is positive if s is in a sentence before q, negative if after and 0 in the same.
        * the number of paragraphs between q and s
            * 0             if s and q are in the same paragraph
            * > 0           if s is in a paragraph before q
            * < 0           if s is in a paragraph after q
        * the number of other sentences that are quotes in between s and q
        * the number of quotes in the 5 paragraphs before q
        * Whether or not s is between quotes.
        * Whether s is in the same sentence as a cue verb

        # TODO: ALL THESE AND FIGURE OUT HOW TO INCLUDE SPACY STUFF (PROBABLY NEED TO HAVE THE DOC AS PARAMETER)
        * Whether s is a descendent of a root verb or descendant of a parataxis
        * Whether s is a subject in the sentence
        * Whether or not s is the descendant of a cue verb

    :param article: models.Article
        The article from which the quote and speakers are taken.
    :param quote_index: int
        The index of the sentence containing a quote in the article.
    :param other_quotes: list(int)
        The index of other sentences containing quotes in the article.
    :param speaker: spaCy.Span
        The span of the speaker.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted
    """
    s_sent = 0
    # The '-  1' is due to speaker.end being the first token after the span
    while s_sent < len(article.sentences['sentences']) and article.sentences['sentences'][s_sent] < speaker.end - 1:
        s_sent = s_sent + 1

    s_par = 0
    while s_par < len(article.paragraphs['paragraphs']) and article.paragraphs['paragraphs'][s_par] < s_sent:
        s_par = s_par + 1

    q_par = 0
    while q_par < len(article.paragraphs['paragraphs']) and article.paragraphs['paragraphs'][q_par] < quote_index:
        q_par = q_par + 1

    sentence_dist = quote_index - s_sent
    paragraph_dist = q_par - s_par

    def separating_quotes():
        sep_quotes = 0
        for other_q in other_quotes:
            if s_sent < other_q < quote_index or s_sent > other_q > quote_index:
                sep_quotes += 1
        return sep_quotes

    def quotes_above_q():
        quotes_above = 0
        for other_q in other_quotes:
            if 0 < quote_index - other_q <= 5:
                quotes_above += 1
        return quotes_above

    speaker_in_quotes = article.in_quotes['in_quotes'][speaker.end - 1]

    def speaker_with_cue_verb():
        sentence_start = 0
        if s_sent > 0:
            sentence_start = article.sentences['sentences'][s_sent - 1] + 1
        sentence_end = article.sentences['sentences'][s_sent]
        tokens = article_doc[sentence_start:sentence_end]
        for token in tokens:
            if token.lemma_ in cue_verbs:
                return True
        return False

    return np.array([
        sentence_dist,
        paragraph_dist,
        separating_quotes(),
        quotes_above_q(),
        speaker_in_quotes,
        speaker_with_cue_verb(),
    ])


def extract_speaker_features_ovo(article, article_doc, quote_index, other_quotes, speaker_1, speaker_2, cue_verbs):
    """
    Gets the features for speaker attribution for a the one vs one case. The following features are taken, for a
    quote q and speakers s1, s2 where q.sent is the index of the sentence containing the quote, s.start is the index of
    the first token of the speaker s, s.end of the last, and s.sent is the index.

    # TODO: For q
    For q:
        * The length of the sentence.
        * Whether it contains quotation marks.
        * If the sentence contains quotation marks:
            * The number of tokens between them.
            * TODO: What if there are multiple quotes in the sentence?
                * Have a fixed number of entries like "tokens between first, second, and third quotes" and most of the
                time second and third are empty?
        * Whether it contains a named entity that is a person.
        * Whether it contains a verb in the verb-cue list.
        * Presence of a parataxis.
        * Presence of multiple verbs.
        * TODO: Presence of a verb in between quotes
        * Is the whole sentence in between quotes
        * The proportion of tokens in the sentence that are between quotes

    For both s1 and s2:
        * the distance between q and s: q.sent - s.sent
            * The value is positive if s is in a sentence before q, negative if after and 0 in the same.
        * the number of paragraphs between q and s
            * 0             if s and q are in the same paragraph
            * > 0           if s is in a paragraph before q
            * < 0           if s is in a paragraph after q
        * the number of other sentences that are quotes in between s and q
        * Whether or not s is between quotes.
        * Whether s is a descendent of a root verb or descendant of a parataxis
        * Whether s is a subject in the sentence
        * Whether or not s is the descendant of a cue verb

    :param article: models.Article
        The article from which the quote and speakers are taken.
    :param quote_index: int
        The index of the sentence containing a quote in the article.
    :param other_quotes: list(int)
        The index of other sentences containing quotes in the article.
    :param speaker_1: spaCy.Span
        The span of the first speaker.
    :param speaker_2: spaCy.Span
        The span of the second speaker.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted
    """
    quote_start = 0
    if quote_index > 0:
        quote_start = article.sentences['sentences'][quote_index - 1] + 1
    quote_end = article.sentences['sentences'][quote_index]
    q_in_quotes = article.in_quotes['in_quotes'][quote_start:quote_end + 1]
    quote_features = extract_quote_features(article_doc[quote_start:quote_end], cue_verbs, q_in_quotes)

    speaker_1_features = extract_single_speaker_features(article, article_doc, quote_index, other_quotes, speaker_1, cue_verbs)
    speaker_2_features = extract_single_speaker_features(article, article_doc, quote_index, other_quotes, speaker_2, cue_verbs)
    return np.concatenate((quote_features, speaker_1_features, speaker_2_features), axis=0)


def extract_speaker_features_complex(p_ends, s_ends, quote_index, other_quotes,
                                        speaker_index, speaker_other_indices, other_speakers):
    """
    Gets the features for speaker attribution for a quote and a speaker. The following features are taken, for a
    quote q and a speaker s, where s_index is the index of the last token of the speaker, quote_start is the index of
    the first token of q, quote_end is the index of the last token of q:
        * the distance between q and s:
            * 0                       if s is in q
            * quote_start - s_index   if s is in a sentence before q (the value will always be positive)
            * quote_end - s_index     if s is in a sentence after q (the value will always be negative)
        * the number of paragraphs between q and s
            * 0             if s and q are in the same paragraph
            * > 0           if s is in a paragraph before q
            * < 0           if s is in a paragraph after q
        * the number of other sentences that are quotes in between s and q
        * the number of other speakers in between s and q
        * the number of mentions of s in the 10 paragraphs before q
        * the number of mentions of other speakers in the 10 paragraphs before q
        * the number of quotes in the 10 paragraphs before q

    :param p_ends: list(int)
        The index of all sentences that are the last in a paragraph.
    :param s_ends: list(int)
        The index of all tokens that are the last in a sentence.
    :param quote_index: int
        The index of the reported speech sentence in the document.
    :param other_quotes: list(int)
        The indices of other sentences in the document that are quotes.
    :param speaker_index: int
        The index of the last token of the speaker in the document.
    :param speaker_other_indices: list(int)
        The indices of other tokens that are the last token for another mention of the same speaker.
    :param other_speakers: list(int)
        The indices of the last token of other speakers in the document.
    :return: np.array
        The features extracted.
    """
    quote_start = 0
    if quote_index > 0:
        quote_start = s_ends[quote_index - 1]
    quote_end = s_ends[quote_index]

    quote_paragraph_index = 0
    while quote_index > p_ends[quote_paragraph_index]:
        quote_paragraph_index += 1

    speaker_sentence_index = 0
    while speaker_index > s_ends[speaker_sentence_index]:
        speaker_sentence_index += 1

    speaker_paragraph_index = 0
    while speaker_sentence_index > p_ends[speaker_paragraph_index]:
        speaker_paragraph_index += 1

    def token_distance():
        """ the distance between q and s """
        if speaker_index < quote_start:
            return quote_start - speaker_index
        elif speaker_index > quote_end:
            return quote_end - speaker_index
        else:
            return 0

    def paragraph_distance():
        """ the number of paragraphs between q and s """
        return quote_paragraph_index - speaker_paragraph_index

    def separating_quotes():
        """ the number of other sentences that are quotes in between s and q """
        sep_quotes = 0
        for other_quote_index in other_quotes:
            if (speaker_sentence_index <= other_quote_index < quote_index) or \
                    (quote_index < other_quote_index <= speaker_sentence_index):
                sep_quotes += 1
        return sep_quotes

    def separating_speakers():
        """ the number of other speakers in between s and q """
        sep_speakers = 0
        for other_speaker_index in other_speakers:
            if (speaker_sentence_index <= other_speaker_index < quote_index) or \
                    (quote_index < other_speaker_index <= speaker_sentence_index):
                sep_speakers += 1
        return sep_speakers

    def mentions(indices):
        first_paragraph = max(0, quote_paragraph_index - 10)
        first_token = 0
        if first_paragraph > 0:
            first_sentence = p_ends[first_paragraph - 1]
            first_token = s_ends[first_sentence - 1]
        person_mentions = 0
        for i in indices:
            if first_token <= i <= quote_start:
                person_mentions += 1
        return person_mentions

    def speaker_mentions():
        """ the number of mentions of s in the 10 paragraphs before q """
        return mentions(speaker_other_indices)

    def other_speaker_mentions():
        """ the number of mentions of other speakers in the 10 paragraphs before q """
        return mentions(other_speakers)

    def other_quote_number():
        """ the number of quotes in the 10 paragraphs before q """
        first_paragraph = max(0, quote_paragraph_index - 10)
        first_sentence = 0
        if first_paragraph > 0:
            first_sentence = p_ends[first_paragraph - 1]
        num_other_quotes = 0
        for i in other_quotes:
            if first_sentence <= i < quote_index:
                num_other_quotes += 1
        return num_other_quotes

    return np.array([
        token_distance(),
        paragraph_distance(),
        separating_quotes(),
        separating_speakers(),
        speaker_mentions(),
        other_speaker_mentions(),
        other_quote_number(),
    ])
