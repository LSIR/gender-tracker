import numpy as np


"""
Contains all methods to extract features from sentences to determine if they contain a quote or not, as well as
methods to extract features to determine speaker extraction for quotes. 
"""


def extract_sentence_features(sentence, cue_verbs):
    """
    Gets features for possible elements in the sentence that can hint to it having a quote:
        * Whether it contains quotation marks.
        * Whether it contains a named entity that is a person.
        * Whether it contains a verb in the verb-cue list.
        * The length of the sentence.

    :param sentence: spaCy.doc.
        The sentence to extract features from.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted.
    """
    contains_quote = '"' in sentence.text
    contains_named_entity = len(sentence.ents) > 0
    contains_cue_verb = False
    contains_pronoun = False
    for token in sentence:
        if token.lemma_ in cue_verbs:
            contains_cue_verb = True
        if token.pos_ == 'PRON':
            contains_pronoun = True
    return np.array([int(contains_quote),
                     int(contains_named_entity),
                     int(contains_cue_verb),
                     int(contains_pronoun)])
