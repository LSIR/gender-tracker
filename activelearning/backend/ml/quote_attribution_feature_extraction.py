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


########################################################################################################################
# One Versus All Quote Attribution

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

        * The number of other speakers named between the first speaker and the quote.
        * The number of other quotes between the first speaker and the quote.
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
        return np.concatenate((features_2, np.array([0, 0])), axis=0)

    s_sent, s_sent_start, s_rel_token_indices = speaker_information(article, speaker)

    quotes_in_between = 0
    for index in other_quotes:
        if s_sent < index < quote_index or s_sent > index > quote_index:
            quotes_in_between += 1

    if abs(s_sent - quote_index) < 2:
        quote_in_between_proportion = 1
    else:
        quote_in_between_proportion = quotes_in_between/(abs(s_sent - quote_index) - 1)

    return np.concatenate((features_2, np.array([
        quotes_in_between,
        quote_in_between_proportion,
    ])), axis=0)


########################################################################################################################
# One vs One (ovo) Quote Attribution

def attribution_features0(article, sentences, quote_index, speaker, other_quotes, cue_verbs):
    """
    Gets the features for speaker attribution for a single speaker, in the one vs one case. The following features are
    taken, for a quote q and a speaker s where q.sent is the index of the sentence containing the quote, s.start is the
    index of the first token of the speaker s, s.end of the last, and s.sent is the index.

    :param article: models.Article
        The article from which the quote and speakers are taken.
    :param sentences: list(spaCy.Doc)
        the spaCy.Doc for each sentence in the article.
    :param quote_index: int
        The index of the sentence containing a quote in the article.
    :param speaker: dict.
        The speaker. Has keys 'name', 'full_name', 'start', 'end', as described in the database.
    :param other_quotes: list(int)
        The index of other sentences containing quotes in the article.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted
    """
    # The index of the sentence in which the speaker is found
    s_sent = 0
    while s_sent < len(article.sentences['sentences']) and article.sentences['sentences'][s_sent] < speaker['end']:
        s_sent = s_sent + 1

    # The index of the first token in the sentence containing the speaker
    speaker_sent_start = 0
    if s_sent > 0:
        speaker_sent_start = article.sentences['sentences'][s_sent - 1] + 1
    # The indices of the tokens of the speaker in it's sentence doc.
    relative_speaker_tokens = [i - speaker_sent_start for i in range(speaker['start'], speaker['end'] + 1)]

    # The index of the paragraph in which the speaker is found
    s_par = 0
    while s_par < len(article.paragraphs['paragraphs']) and article.paragraphs['paragraphs'][s_par] < s_sent:
        s_par = s_par + 1

    # The index of the paragraph in which the quote is found
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
            if 0 < quote_index - other_q <= 10:
                quotes_above += 1
        return quotes_above

    speaker_in_quotes = article.in_quotes['in_quotes'][speaker['end']]

    def speaker_with_cue_verb():
        tokens = sentences[s_sent]
        for token in tokens:
            if token.lemma_ in cue_verbs:
                return 1
        return 0

    def speaker_dep(dep):
        for index in relative_speaker_tokens:
            if sentences[s_sent][index].dep_ == dep:
                return 1
        return 0

    def child_of_cue_verb():
        speaker_sentence = sentences[s_sent]
        for token in speaker_sentence:
            if token.lemma_ in cue_verbs:
                for child in token.children:
                    if child.i in relative_speaker_tokens:
                        return 1
        return 0

    return np.array([
        s_sent,
        quote_index,
        s_par,
        q_par,
        sentence_dist,
        paragraph_dist,
        separating_quotes(),
        quotes_above_q(),
        speaker_in_quotes,
        speaker_with_cue_verb(),
        speaker_dep('nsubj'),
        speaker_dep('obj'),
        child_of_cue_verb(),
    ])
