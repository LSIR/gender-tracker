import numpy as np


"""
Contains all methods to extract features from sentences to determine if they contain a quote or not, as well as
methods to extract features to determine speaker extraction for quotes. 
"""

""" The number of features used to detect if a sentence contains reported speech. """
QUOTE_FEATURES = 6

""" The number of features used to detect if a named entity is the author of reported speech. """
SPEAKER_FEATURES = 7


def extract_quote_features(sentence, cue_verbs):
    """
    Gets features for possible elements in the sentence that can hint to it having a quote:
        * The length of the sentence.
        * Whether it contains quotation marks.
        * Whether it contains a named entity that is a person.
        * Whether it contains a verb in the verb-cue list.
        * Presence of a parataxis.
        * Presence of multiple verbs.

    :param sentence: spaCy.doc.
        The sentence to extract features from.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted.
    """
    contains_quote = int('"' in sentence.text)
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

    return np.array([
        len(sentence),
        contains_quote,
        contains_named_entity,
        contains_cue_verb(),
        contains_pronoun(),
        contains_parataxis()
    ])


def extract_speaker_features(p_ends, s_ends, quote_index, other_quotes,
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
        * whether the tokens before/after the speaker/quote is:
            * punctuation
            * the last token of the quote
            * a different speaker
            * a different quote
            * a reported speech verb

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
