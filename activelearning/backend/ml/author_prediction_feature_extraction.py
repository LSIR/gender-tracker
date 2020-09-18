import numpy as np
from backend.ml.quote_attribution_feature_extraction import speaker_information


def attribution_features_baseline(article, sentences, quotes, speaker, other_speakers, cue_verbs):
    """
    First feature extraction model for author prediction. Extracts the following features for a named entity.

    Boolean features:
        * Whether or not the speaker is the subject of the sentence
        * Whether or not the speaker is the object of the sentence
        * Whether or not the speaker is in a sentence containing a cue verb
        * Whether or not the speaker is in a sentence containing a reported speech
        * Whether or not the speaker is in a sentence containing a parataxis
        * Whether or not the speaker is between quotation marks
        * Whether there is any reported speech above the speaker
        * Whether there is any reported speech below the speaker

    Other features:
        * Number of sentences between the speaker and the closest reported speech sentence above it. 100 if none.
        * Number of sentences between the speaker and the closest reported speech sentence below it. 100 if none.
        * Number of other speakers between it and the closest quote above it.
        * Number of other speakers between it and the closest quote below it.
        * Number of quotes within 3 sentences above it
        * Number of quotes within 3 sentences below it
        * Number of quotes within 6 sentences above it
        * Number of quotes within 6 sentences below it
        * Number of other speakers within 3 sentences above it
        * Number of other speakers within 3 sentences below it
        * Number of other speakers within 6 sentences above it
        * Number of other speakers within 6 sentences below it

    :param article: models.Article
        The article from which the quote and speakers are taken.
    :param sentences: list(spaCy.Doc)
        the spaCy.Doc for each sentence in the article.
    :param quotes: list(int)
        The indices of other sentences that are quotes in the article.
    :param speaker: dict.
        The speaker. Has keys 'name', 'full_name', 'start', 'end', as described in the database.
    :param other_speakers: list(dict)
        The list of other speakers in the article.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted
    """
    speaker_sent_index, speaker_first_token_index, relative_token_indices = speaker_information(article, speaker)

    # Boolean features

    def speaker_dep(dep):
        for index in relative_token_indices:
            if sentences[speaker_sent_index][index].dep_ == dep:
                return 1
        return 0

    def speaker_with_cue_verb():
        tokens = sentences[speaker_sent_index]
        for token in tokens:
            if token.lemma_ in cue_verbs:
                return 1
        return 0

    def speaker_with_rs():
        return int(speaker_sent_index in quotes)

    def contains_parataxis():
        tokens = sentences[speaker_sent_index]
        for token in tokens:
            if token.dep_ == 'parataxis':
                return 1
        return 0

    def speaker_in_quotes():
        return article.in_quotes['in_quotes'][speaker_first_token_index] == 1

    def rs_before_speaker():
        if len(quotes) == 0:
            return 0
        return int(quotes[0] < speaker_sent_index)

    def rs_after_speaker():
        if len(quotes) == 0:
            return 0
        return int(quotes[-1] > speaker_sent_index)

    # Other features
    other_speaker_sentences = [speaker_information(article, other_speaker)[0] for other_speaker in other_speakers]

    def closest_rs_above():
        if len(quotes) == 0 or quotes[0] >= speaker_sent_index:
            return None
        else:
            i = -1
            while i < len(quotes) - 1 and quotes[i + 1] < speaker_sent_index:
                i += 1

            return quotes[i]

    index_closest_rs_above = closest_rs_above()

    def dist_to_closest_rs_above():
        if index_closest_rs_above:
            return speaker_sent_index - index_closest_rs_above
        else:
            return 100

    def closest_rs_below():
        if len(quotes) == 0 or quotes[-1] <= speaker_sent_index:
            return None
        else:
            i = len(quotes)
            while i > 0 and quotes[i - 1] > speaker_sent_index:
                i -= 1

            return quotes[i]

    index_closest_rs_below = closest_rs_below()

    def dist_to_closest_rs_below():
        if index_closest_rs_below:
            return index_closest_rs_below - speaker_sent_index
        else:
            return 100

    def speakers_between_quote_above():
        if index_closest_rs_above:
            other_speakers_between = 0
            for other_sent_index in other_speaker_sentences:
                if index_closest_rs_above <= other_sent_index < speaker_sent_index:
                    other_speakers_between += 1
            return other_speakers_between
        else:
            return 0

    def speakers_between_quote_below():
        if index_closest_rs_below:
            other_speakers_between = 0
            for other_sent_index in other_speaker_sentences:
                if index_closest_rs_below >= other_sent_index > speaker_sent_index:
                    other_speakers_between += 1
            return other_speakers_between
        else:
            return 0

    def quotes_n_above(n):
        if len(quotes) == 0 or quotes[0] >= speaker_sent_index:
            return 0

        quotes_n_above_speak = 0
        i = 0
        while i < len(quotes) and quotes[i] < speaker_sent_index:
            if 0 < speaker_sent_index - quotes[i] <= n:
                quotes_n_above_speak += 1
            i += 1
        return quotes_n_above_speak

    def quotes_n_below(n):
        if len(quotes) == 0 or quotes[-1] <= speaker_sent_index:
            return 0

        quotes_n_below_speak = 0
        i = len(quotes) - 1
        while i >= 0 and quotes[i] > speaker_sent_index:
            if 0 < quotes[i] - speaker_sent_index <= n:
                quotes_n_below_speak += 1
            i -= 1
        return quotes_n_below_speak

    def speakers_n_above(n):
        if len(other_speaker_sentences) == 0 or other_speaker_sentences[0] >= speaker_sent_index:
            return 0

        speakers_n_above_speak = 0
        i = 0
        while i < len(other_speaker_sentences) and other_speaker_sentences[i] < speaker_sent_index:
            if 0 < speaker_sent_index - other_speaker_sentences[i] <= n:
                speakers_n_above_speak += 1
            i += 1
        return speakers_n_above_speak

    def speakers_n_below(n):
        if len(other_speaker_sentences) == 0 or other_speaker_sentences[-1] <= speaker_sent_index:
            return 0

        speakers_n_below_speak = 0
        i = len(other_speaker_sentences) - 1
        while i >= 0 and other_speaker_sentences[i] > speaker_sent_index:
            if 0 < other_speaker_sentences[i] - speaker_sent_index <= n:
                speakers_n_below_speak += 1
            i -= 1
        return speakers_n_below_speak

    return np.array([
        speaker_dep('nsubj'),
        speaker_dep('obj'),
        speaker_with_cue_verb(),
        speaker_with_rs(),
        contains_parataxis(),
        speaker_in_quotes(),
        rs_before_speaker(),
        rs_after_speaker(),
        dist_to_closest_rs_above(),
        dist_to_closest_rs_below(),
        speakers_between_quote_above(),
        speakers_between_quote_below(),
        quotes_n_above(3),
        quotes_n_below(3),
        quotes_n_above(6),
        quotes_n_below(6),
        speakers_n_above(3),
        speakers_n_below(3),
        speakers_n_above(6),
        speakers_n_below(6),
    ])
