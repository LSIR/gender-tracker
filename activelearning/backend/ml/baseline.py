from sklearn.metrics import precision_recall_fscore_support

from backend.db_management import load_labeled_articles, load_quote_authors
from backend.helpers import aggregate_label
import numpy as np

from backend.ml.helpers import find_true_author_index, extract_speaker_names, evaluate_speaker_extraction
from backend.ml.scoring import Results

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


def predict_sentence(sent_span, in_quotes):
    """
    Rule-based model to determine if a sentence contains reported speech or not. Rule:

        A sentence is determined to contain reported speech if and only if it contains a piece of text of at least 3
        tokens between quotes, where all tokens between quotes aren't capitalized.

    :param sent_span: spaCy.Doc
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


def baseline_quote_detection(nlp):
    """
    Evaluates the baseline model for quote detection.

    :param nlp: spaCy.Language
        The language model used to tokenize the text.
    :return: QuoteDetectionDataset
        The dataset that was used for quote detection.
    """
    y = []
    y_pred = []
    train_articles, train_sentences, _, _ = load_labeled_articles(nlp)
    for index, article in enumerate(train_articles):
        article_sentences = train_sentences[index]
        sentence_start = 0
        for sentence_index, end in enumerate(article.sentences['sentences']):
            sentence_labels, sentence_authors, _ = aggregate_label(article, sentence_index)
            true_value = int(sum(sentence_labels) > 0)
            y.append(true_value)

            in_quotes = article.in_quotes['in_quotes'][sentence_start:end + 1]
            prediction = predict_sentence(article_sentences[sentence_index], in_quotes)
            y_pred.append(prediction)

            sentence_start = end + 1

    accuracy = np.sum(np.equal(y, y_pred))/len(y)
    precision, recall, f1, _ = precision_recall_fscore_support(y, y_pred, zero_division=0, average='binary')
    scores = Results()
    scores.add_scores({
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
    })
    return scores


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
    index = token.i
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
    return [index + sentence_start for index in relative_indices]


def attribute_quote(all_sentences, sentence_index, sentence_starts, in_quotes, cue_verbs):
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


def attribute_quote_lazy(all_sentences, sentence_index, sentence_starts, in_quotes, cue_verbs):
    """
    Lazy version of the baseline quote attribution model. This model only selects a named entity for the quote if the
    sentence containing the quote contains a cue verb which has a named entity as a child, or if the sentence containing
    the quote contains a named entity that isn't between quotes. Otherwise returns that the quote has no author

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

    # The sentence has no named entity as an author
    return []


def baseline_quote_attribution(nlp, cue_verbs):
    """
    Evaluates the baseline model for quote attribution.

    :param nlp: spaCy.Language
        The language model used to tokenize the text.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return:
    """
    y = []
    y_pred = []
    y_pred_lazy = []
    average_precision = []
    average_recall = []
    average_precision_lazy = []
    average_recall_lazy = []
    train_dicts, _ = load_quote_authors(nlp)
    for i, article_dict in enumerate(train_dicts):
        mentions = article_dict['article'].people['mentions']
        sentence_ends = article_dict['article'].sentences['sentences']
        sentence_starts = [0] + [s_end + 1 for s_end in sentence_ends][:-1]
        sentence_edges = zip(sentence_starts, sentence_ends)
        in_quotes = []
        for start, end in sentence_edges:
            in_quotes.append(article_dict['article'].in_quotes['in_quotes'][start:end + 1])

        article_labels = []
        article_predictions = []
        article_predictions_lazy = []
        sentences = article_dict['sentences']
        for j, sent_index in enumerate(article_dict['quotes']):
            true_author = article_dict['authors'][j]
            true_mention_index = find_true_author_index(true_author, mentions)
            article_labels.append(true_mention_index)

            predicted_author = attribute_quote(sentences, sent_index, sentence_starts, in_quotes, cue_verbs)
            predicted_index = find_true_author_index(predicted_author, mentions)
            article_predictions.append(predicted_index)

            predicted_author_lazy = attribute_quote_lazy(sentences, sent_index, sentence_starts, in_quotes, cue_verbs)
            predicted_index_lazy = find_true_author_index(predicted_author_lazy, mentions)
            article_predictions_lazy.append(predicted_index_lazy)

        true_names = extract_speaker_names(article_dict['article'], article_labels)

        predicted_names = extract_speaker_names(article_dict['article'], article_predictions)
        precision, recall = evaluate_speaker_extraction(true_names, predicted_names)
        average_precision.append(precision)
        average_recall.append(recall)

        predicted_names_lazy = extract_speaker_names(article_dict['article'], article_predictions_lazy)
        precision, recall = evaluate_speaker_extraction(true_names, predicted_names_lazy)
        average_precision_lazy.append(precision)
        average_recall_lazy.append(recall)

        y += article_labels
        y_pred += article_predictions
        y_pred_lazy += article_predictions_lazy

    accuracy = np.sum(np.equal(y, y_pred)) / len(y)
    print(f'    Accuracy: {round(accuracy, 3)}')
    accuracy_lazy = np.sum(np.equal(y, y_pred_lazy)) / len(y)
    print(f'    Accuracy Lazy: {round(accuracy_lazy, 3)}')
    precision = np.sum(average_precision) / len(average_precision)
    recall = np.sum(average_recall) / len(average_recall)
    print(f'    Average scores for speakers extracted from articles')
    print(f'        Precision: {round(precision, 3)}')
    print(f'        Recall:    {round(recall, 3)}')
    precision = np.sum(average_precision_lazy) / len(average_precision_lazy)
    recall = np.sum(average_recall_lazy) / len(average_recall_lazy)
    print(f'        Lazy Precision: {round(precision, 3)}')
    print(f'        Lazy Recall:    {round(recall, 3)}')
    return accuracy





















