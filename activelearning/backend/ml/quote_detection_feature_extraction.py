import numpy as np


def feature_extraction(sentence, cue_verbs, in_quotes):
    """
    Gets features for possible elements in the sentence that can hint to it having a quote:

    :param sentence: spaCy.doc.
        The sentence to extract features from.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :param in_quotes: list(int).
        Whether each token in the sentence is between quotes or not
    :return: np.array
        The features extracted.
    """
    sentence_length = len(sentence)
    contains_quote = int('"' in sentence.text)
    tokens_inside_quote = sum(in_quotes)
    contains_named_entity = int(len(sentence.ents) > 0)
    contains_per_named_entity = int(len([ne for ne in sentence.ents if ne.label_ == 'PER']) > 0)
    sentence_inside_quotes = int(len(in_quotes) == sum(in_quotes))
    inside_quote_proportion = sum(in_quotes)/len(in_quotes)

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

    def number_of_verbs():
        verbs = 0
        for token in sentence:
            if token.pos_ == 'VERB':
                verbs += 1
        return verbs

    def verb_inside_quotes():
        for index, token in enumerate(sentence):
            if token.pos_ == 'VERB' and in_quotes[index] == 1:
                return 1
        return 0

    def contains_selon():
        for token in sentence:
            if token.text.lower() == 'selon':
                return True
        return False

    return np.array([
        sentence_length,
        contains_quote,
        tokens_inside_quote,
        contains_named_entity,
        contains_per_named_entity,
        contains_cue_verb(),
        contains_pronoun(),
        contains_parataxis(),
        number_of_verbs(),
        verb_inside_quotes(),
        sentence_inside_quotes,
        inside_quote_proportion,
        contains_selon(),
    ])