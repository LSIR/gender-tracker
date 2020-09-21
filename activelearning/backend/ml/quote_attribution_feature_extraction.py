import numpy as np


def speaker_information(article, speaker):
    """
    Extracts information about the speaker and the sentence containing it.

    :param article: models.Article
        The article from which the speaker is taken.
    :param speaker: dict.
        The speaker. Has keys 'name', 'full_name', 'start', 'end', as described in the database.
    :return: int, int, int
        * The index of the sentence containing the speaker
        * The index of the first token in the sentence containing the speaker
        * The indices of the tokens of the speaker in the sentence's doc.
    """
    # The index of the speaker containing the quote.
    sent = 0
    while sent < len(article.sentences['sentences']) and article.sentences['sentences'][sent] < speaker['end']:
        sent = sent + 1

    # The index of the first token in the sentence containing the speaker
    sent_start = 0
    if sent > 0:
        sent_start = article.sentences['sentences'][sent - 1] + 1
    rel_token_indices = [i - sent_start for i in range(speaker['start'], speaker['end'] + 1)]

    return sent, sent_start, rel_token_indices


def speaker_information_no_db(sentence_indices, speaker):
    """
    Extracts information about the speaker and the sentence containing it.

    :param sentence_indices: list(int)
        The index of the first token of each sentence in the article, as in article.sentences['sentences']
    :param speaker: dict.
        The speaker. Has keys 'name', 'full_name', 'start', 'end', as described in the database.
    :return: int, int, int
        * The index of the sentence containing the speaker
        * The index of the first token in the sentence containing the speaker
        * The indices of the tokens of the speaker in the sentence's doc.
    """
    # The index of the speaker containing the quote.
    sent = 0
    while sent < len(sentence_indices) and sentence_indices[sent] < speaker['end']:
        sent = sent + 1

    # The index of the first token in the sentence containing the speaker
    sent_start = 0
    if sent > 0:
        sent_start = sentence_indices[sent - 1] + 1
    rel_token_indices = [i - sent_start for i in range(speaker['start'], speaker['end'] + 1)]

    return sent, sent_start, rel_token_indices


########################################################################################################################
# One Versus All Quote Attribution


def attribution_features_baseline(article, sentences, quote_index, speaker, other_speakers, cue_verbs):
    """
    First feature extraction model for quote attribution. Extracts the following features for a quote and a speaker:

        * A first boolean feature to mark weasel features.
        * Boolean features indicating:
            * Whether the speaker is in the same sentence as the quote
            * Whether the sentence containing a quote contains a cue verb
            * Whether the speaker is in between quotation marks
            * Whether the speaker is the first named entity in a sentence above the quote

            * Whether ANOTHER speaker is in the same sentence as the quote, and isn't between quotation marks

    :param article: models.Article
        The article from which the quote and speakers are taken.
    :param sentences: list(spaCy.Doc)
        the spaCy.Doc for each sentence in the article.
    :param quote_index: int
        The index of the sentence containing a quote in the article.
    :param speaker: dict.
        The speaker. Has keys 'name', 'full_name', 'start', 'end', as described in the database.
    :param other_speakers: list(dict)
        The list of other speakers in the article.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted
    """
    if speaker is None:
        return np.array([0, 0, 0, 0, 0, 0])

    speaker_sent, speaker_first_token_index, _ = speaker_information(article, speaker)

    in_same_sentence = (quote_index == speaker_sent)

    def speaker_in_quotes():
        return article.in_quotes['in_quotes'][speaker_first_token_index] == 1

    def speaker_with_cue_verb():
        tokens = sentences[speaker_sent]
        for token in tokens:
            if token.lemma_ in cue_verbs:
                return 1
        return 0

    other_speaker_info = [speaker_information(article, speaker) for speaker in other_speakers]

    def first_named_entity_above():
        if speaker_sent < quote_index:
            for sent, _, _ in other_speaker_info:
                if speaker_sent < sent < quote_index:
                    return 0
            return 1
        return 0

    def other_speaker_in_quote():
        for sent, start_token, _ in other_speaker_info:
            if sent == quote_index and article.in_quotes['in_quotes'][start_token] == 0:
                return 1
        return 0

    return np.array([
        1,
        in_same_sentence,
        speaker_with_cue_verb(),
        speaker_in_quotes(),
        first_named_entity_above(),
        other_speaker_in_quote(),
    ])


def attribution_features_baseline_expanded(article, sentences, quote_index, speaker, other_quotes, other_speakers, cue_verbs):
    """
    First feature extraction model for quote attribution. Extracts the following features for a quote and a speaker:

        * A first boolean feature to mark weasel features.
        * Boolean features indicating:
            * Whether the speaker is in the same sentence as the quote
            * Whether the sentence containing a quote contains a cue verb
            * Whether the speaker is in between quotation marks
            * Whether the speaker is the first named entity in a sentence above the quote

            * Whether ANOTHER speaker is in the same sentence as the quote, and isn't between quotation marks

            * Whether the speaker is a subject in the sentence
            * Whether the speaker is an object in the sentence

        * Features indicating:
            * The number of sentences between the speaker and the quote that don't contain quotes
            * The number of named entities between the speaker and the quote

    :param article: models.Article
        The article from which the quote and speakers are taken.
    :param sentences: list(spaCy.Doc)
        the spaCy.Doc for each sentence in the article.
    :param quote_index: int
        The index of the sentence containing a quote in the article.
    :param speaker: dict.
        The speaker. Has keys 'name', 'full_name', 'start', 'end', as described in the database.
    :param other_quotes: list(dict)
        The list of other speakers in the article.
    :param other_speakers: list(dict)
        The list of other speakers in the article.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted
    """
    if speaker is None:
        return np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    speaker_sent, speaker_first_token_index, s_rel_token_indices = speaker_information(article, speaker)

    in_same_sentence = (quote_index == speaker_sent)

    def speaker_in_quotes():
        return article.in_quotes['in_quotes'][speaker_first_token_index] == 1

    def speaker_with_cue_verb():
        tokens = sentences[speaker_sent]
        for token in tokens:
            if token.lemma_ in cue_verbs:
                return 1
        return 0

    other_speaker_info = [speaker_information(article, speaker) for speaker in other_speakers]
    other_speaker_sentences = [speaker_info[0] for speaker_info in other_speaker_info]
    other_speaker_start_tokens = [speaker_info[1] for speaker_info in other_speaker_info]

    def first_named_entity_above():
        if speaker_sent < quote_index:
            for sent in other_speaker_sentences:
                if speaker_sent < sent < quote_index:
                    return 0
            return 1
        return 0

    def other_speaker_in_quote():
        for sent, start_token in zip(other_speaker_sentences, other_speaker_start_tokens):
            if sent == quote_index and article.in_quotes['in_quotes'][start_token] == 0:
                return 1
        return 0

    def speaker_dep(dep):
        for index in s_rel_token_indices:
            if sentences[speaker_sent][index].dep_ == dep:
                return 1
        return 0

    def num_sentences_separating():
        quotes_between = 0
        for q in other_quotes:
            if speaker_sent < q < quote_index or speaker_sent > q > quote_index:
                quotes_between += 1
        return quote_index - speaker_sent - quotes_between

    def speakers_between_speaker_and_quote():
        speakers_between = 0
        for sent in other_speaker_sentences:
            if speaker_sent < sent < quote_index or speaker_sent > sent > quote_index:
                speakers_between += 1
        return speakers_between

    return np.array([
        1,
        in_same_sentence,
        speaker_with_cue_verb(),
        speaker_in_quotes(),
        first_named_entity_above(),
        other_speaker_in_quote(),
        speaker_dep('nsubj'),
        speaker_dep('obj'),
        num_sentences_separating(),
        speakers_between_speaker_and_quote(),
    ])


def attribution_features_1(article, sentences, quote_index, speaker, cue_verbs):
    """
    First feature extraction model for quote attribution. Extracts the following features for a quote and a speaker:

        * A first boolean feature to mark weasel features.
        * A feature containing the number of sentences between the sentence containing the quote and the sentence
        containing the feature.
        * A feature containing whether the sentence containing the speaker also contains a cue verb.

    :param article: models.Article
        The article from which the quote and speakers are taken.
    :param sentences: list(spaCy.Doc)
        the spaCy.Doc for each sentence in the article.
    :param quote_index: int
        The index of the sentence containing a quote in the article.
    :param speaker: dict.
        The speaker. Has keys 'name', 'full_name', 'start', 'end', as described in the database.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted
    """
    if speaker is None:
        return np.array([0, 0, 0])

    speaker_sent, _, _ = speaker_information(article, speaker)
    s1_dist = quote_index - speaker_sent

    def speaker_with_cue_verb():
        tokens = sentences[speaker_sent]
        for token in tokens:
            if token.lemma_ in cue_verbs:
                return 1
        return 0

    return np.array([
        1,
        s1_dist,
        speaker_with_cue_verb(),
    ])


def attribution_features_2(article, sentences, quote_index, speaker, other_quotes, other_speakers, cue_verbs):
    """
    Second feature extraction model for quote attribution. Extracts the same features as the first model, plus:

        * The number of other speakers named between the speaker and the quote.
        * The number of other quotes between the speaker and the quote.
        * Whether the speaker is an object in it's sentence
        * Whether the speaker is a subject in it's sentence

    :param article: models.Article
        The article from which the quote and speakers are taken.
    :param sentences: list(spaCy.Doc)
        the spaCy.Doc for each sentence in the article.
    :param quote_index: int
        The index of the sentence containing a quote in the article.
    :param speaker: dict.
        The speaker. Has keys 'name', 'full_name', 'start', 'end', as described in the database.
    :param other_quotes: list(int)
        The indices of other sentences that are quotes in the article.
    :param other_speakers: list(dict)
        The list of other speakers in the article.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted
    """
    features_1 = attribution_features_1(article, sentences, quote_index, speaker, cue_verbs)

    if speaker is None:
        return np.concatenate((features_1, np.array([0, 0, 0, 0])), axis=0)

    s_sent, s_sent_start, s_rel_token_indices = speaker_information(article, speaker)

    other_speaker_sentences = [speaker_information(article, speaker)[0] for speaker in other_speakers]
    speakers_between = 0
    for s in other_speaker_sentences:
        if s_sent < s < quote_index or s_sent > s > quote_index:
            speakers_between += 1

    quotes_between = 0
    for q in other_quotes:
        if s_sent < q < quote_index or s_sent > q > quote_index:
            quotes_between += 1

    def speaker_dep(dep):
        for index in s_rel_token_indices:
            if sentences[s_sent][index].dep_ == dep:
                return 1
        return 0

    return np.concatenate((features_1, np.array([
        speakers_between,
        quotes_between,
        speaker_dep('nsubj'),
        speaker_dep('obj'),
    ])), axis=0)


########################################################################################################################
# One Versus One Quote Attribution

def attribution_features_ovo_1(article, sentences, quote_index, speaker, cue_verbs):
    """
    First feature extraction model for quote attribution. Extracts the following features for a quote and a speaker:

        * A first boolean feature to mark weasel features.
        * A feature containing the number of sentences between the sentence containing the quote and the sentence
        containing the feature.
        * A feature containing whether the sentence containing the speaker also contains a cue verb.

    :param article: models.Article
        The article from which the quote and speakers are taken.
    :param sentences: list(spaCy.Doc)
        the spaCy.Doc for each sentence in the article.
    :param quote_index: int
        The index of the sentence containing a quote in the article.
    :param speaker: dict.
        The speaker. Has keys 'name', 'full_name', 'start', 'end', as described in the database.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted
    """
    if speaker is None:
        return np.array([0, 0, 0])

    speaker_sent, _, _ = speaker_information(article, speaker)
    s1_dist = quote_index - speaker_sent

    def speaker_with_cue_verb():
        tokens = sentences[speaker_sent]
        for token in tokens:
            if token.lemma_ in cue_verbs:
                return 1
        return 0

    return np.array([
        1,
        s1_dist,
        speaker_with_cue_verb(),
    ])


def attribution_features_ovo_2(article, sentences, quote_index, speaker, cue_verbs):
    """
    Second feature extraction model for quote attribution. Extracts the same features as the first model, plus:

        * Whether the speaker is an object in it's sentence
        * Whether the speaker is a subject in it's sentence

    :param article: models.Article
        The article from which the quote and speakers are taken.
    :param sentences: list(spaCy.Doc)
        the spaCy.Doc for each sentence in the article.
    :param quote_index: int
        The index of the sentence containing a quote in the article.
    :param speaker: dict.
        The speaker. Has keys 'name', 'full_name', 'start', 'end', as described in the database.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted
    """
    features_1 = attribution_features_ovo_1(article, sentences, quote_index, speaker, cue_verbs)

    if speaker is None:
        return np.concatenate((features_1, np.array([0, 0])), axis=0)

    s_sent, s_sent_start, s_rel_token_indices = speaker_information(article, speaker)

    def speaker_dep(dep):
        for index in s_rel_token_indices:
            if sentences[s_sent][index].dep_ == dep:
                return 1
        return 0

    return np.concatenate((features_1, np.array([
        speaker_dep('nsubj'),
        speaker_dep('obj'),
    ])), axis=0)


def attribution_features_ovo_3(article, sentences, quote_index, speaker, cue_verbs, other_quotes):
    """
    Third feature extraction model for quote attribution. Extracts the same features as the second model, plus:

        * The number of quotes between the speaker and the target quote.
        * The proportion of sentences that are quotes between the speaker and the sentence containing the quote. This
        value is set to 1 if the speaker and the quote are in the same sentence or adjacent sentences.
        * Boolean feature indicating if the speaker is the descendant of a cue verb

    :param article: models.Article
        The article from which the quote and speakers are taken.
    :param sentences: list(spaCy.Doc)
        the spaCy.Doc for each sentence in the article.
    :param quote_index: int
        The index of the sentence containing a quote in the article.
    :param speaker: dict.
        The speaker. Has keys 'name', 'full_name', 'start', 'end', as described in the database.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :param other_quotes: list(int)
        The index of other sentences containing quotes in the article.
    :return: np.array
        The features extracted
    """
    features_2 = attribution_features_ovo_2(article, sentences, quote_index, speaker, cue_verbs)

    if speaker is None:
        return np.concatenate((features_2, np.array([0, 0, 0])), axis=0)

    s_sent, s_sent_start, s_rel_token_indices = speaker_information(article, speaker)

    quotes_in_between = 0
    for index in other_quotes:
        if s_sent < index < quote_index or s_sent > index > quote_index:
            quotes_in_between += 1

    if abs(s_sent - quote_index) < 2:
        quote_in_between_proportion = 1
    else:
        quote_in_between_proportion = quotes_in_between/(abs(s_sent - quote_index) - 1)

    def child_of_cue_verb():
        speaker_sentence = sentences[s_sent]
        for token in speaker_sentence:
            if token.lemma_ in cue_verbs:
                for child in token.children:
                    if child.i in s_rel_token_indices:
                        return 1
        return 0

    return np.concatenate((features_2, np.array([
        quotes_in_between,
        quote_in_between_proportion,
        child_of_cue_verb(),
    ])), axis=0)
