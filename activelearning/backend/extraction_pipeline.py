import csv

import numpy as np
from sklearn.preprocessing import PolynomialFeatures

from backend.ml.author_prediction_feature_extraction import attribution_features_baseline_no_db
from backend.ml.baseline import predict_sentence, attribute_quote_lazy
from backend.ml.helpers import load_model, author_full_name_no_db, find_true_author_index
from backend.ml.quote_detection import predict_quotes
from backend.xml_parsing.xml_to_postgre import process_article, extract_sentence_spans
from backend.xml_parsing.helpers import load_nlp

"""
Pipeline the names of people cited from an article
"""


""" The path to the file containing the weights for the trained quote detection model. """
path_quote_detection_weights = "backend/ml/quote_detection_weights.joblib"


""""""
quote_detection_poly_degree = 2


""" The path to the file containing the weights for the trained author prediction model. """
path_author_attribution_weights = "backend/ml/author_prediction_weights.joblib"


""""""
author_prediction_poly_degree = 5


def extract_people_quoted(article_text, nlp, cue_verbs, lazy_baseline=True):
    """
    Uses

    :param article_text: string
        The article, in XML format (as extracted from websites).
    :param nlp: spaCy.Language.
        The language model used to tokenize the text.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param lazy_baseline: bool.
        If the lazy abseline should be used instead of the ML model.
    :return: list(String)
        The names of all people that are predicted to have been cited in the article.
    """
    if lazy_baseline:
        return extract_people_quoted_baseline(article_text, nlp, cue_verbs)
        
    # Parses the article
    article_text = article_text.replace('&', '&amp;')
    data = process_article(article_text, nlp)
    article_mentions = data['mentions']
    article_sentences = data['s']
    article_in_quotes = data['in_quotes']
    article_sentence_docs = extract_sentence_spans(article_text, nlp)

    # Loads quote detection model and author extraction model
    quote_detection_model = load_model(path_quote_detection_weights)
    author_extraction_model = load_model(path_author_attribution_weights)

    # Computes the in_quotes value for each sentence
    sentence_in_quotes = []
    sentence_start = 0
    for sentence_index, end in enumerate(article_sentences):
        sentence_in_quotes.append(article_in_quotes[sentence_start:end + 1])
        sentence_start = end + 1

    # Predict if each sentence contains a quote or not
    qd_poly = PolynomialFeatures(quote_detection_poly_degree, interaction_only=True, include_bias=True)
    sentence_predictions = predict_quotes(
        quote_detection_model,
        article_sentence_docs,
        cue_verbs,
        sentence_in_quotes,
        proba=False,
        poly=qd_poly
    )

    # predict_quotes returns a the distance from the boundary for SVM, probability for logistic regression
    sentence_predictions = [int(pred > 0) for pred in sentence_predictions]

    # DEBUGGING CODE
    """
    for pred, (s, in_q) in zip(sentence_predictions, zip(article_sentence_docs, sentence_in_quotes)):
        print()
        print(pred)
        print(s)
        print(in_q)
    print()
    """

    # The indices of the sentences predicted to contain quotes in the article.
    indices_sentences_containing_quotes = [index for index, contains_quote in enumerate(sentence_predictions)
                                           if contains_quote == 1]

    # Determining authors
    ap_poly = PolynomialFeatures(author_prediction_poly_degree, interaction_only=True, include_bias=True)
    ap_features = []
    for i, speaker in enumerate(article_mentions):
        speaker_features = attribution_features_baseline_no_db(
            article_sentences,
            article_in_quotes,
            article_sentence_docs,
            indices_sentences_containing_quotes,
            speaker,
            article_mentions[:i] + article_mentions[i + 1:],
            cue_verbs
        )
        speaker_features = ap_poly.fit_transform(speaker_features.reshape((-1, 1))).reshape((-1,))
        ap_features.append(
            speaker_features
        )

    predicted_labels = author_extraction_model.predict(np.array(ap_features))

    # DEBUGGING CODE
    """
    for speaker, label in zip(article_mentions, predicted_labels):
        print()
        print(label)
        print(speaker)
    print()
    """

    speakers = set()
    for i, label in enumerate(predicted_labels):
        if label == 1:
            full_name = author_full_name_no_db(article_mentions, i)
            if full_name is not None and full_name not in speakers:
                speakers.add(full_name)

    predicted_experts = list(speakers)

    return predicted_experts


def test():
    print(f'Loading article...')
    #test_article_url = 'data/parisien/article_00003.xml'
    test_article_url = 'data/parisien/article_00000_test.xml'
    with open(test_article_url, 'r') as file:
        article_text = file.read()

    print(f'Loading language model...')
    nlp = load_nlp()

    print(f'Loading cue verbs...\n\n')
    with open('data/cue_verbs.csv', 'r') as f:
        reader = csv.reader(f)
        cue_verbs = set(list(reader)[0])

    print("Authors:", extract_people_quoted(article_text, nlp, cue_verbs))


def extract_people_quoted_baseline(article_text, nlp, cue_verbs):
    """
    Uses

    :param article_text: string
        The article, in XML format (as extracted from websites).
    :param nlp: spaCy.Language.
        The language model used to tokenize the text.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :return: list(String)
        The names of all people that are predicted to have been cited in the article.
    """
    # Parses the article
    article_text = article_text.replace('&', '&amp;')
    data = process_article(article_text, nlp)
    article_mentions = data['mentions']
    article_sentences = data['s']
    article_in_quotes = data['in_quotes']
    article_sentence_docs = extract_sentence_spans(article_text, nlp)

    # Computes the in_quotes value for each sentence
    sentence_in_quotes = []
    sentence_start = 0
    for end in article_sentences:
        sentence_in_quotes.append(article_in_quotes[sentence_start:end + 1])
        sentence_start = end + 1

    # Predict if each sentence contains a quote or not
    sentence_predictions = []
    for i, sentence_doc in enumerate(article_sentence_docs):
        sentence_predictions.append(predict_sentence(sentence_doc, sentence_in_quotes[i]))

    # The indices of the sentences predicted to contain quotes in the article.
    indices_sentences_containing_quotes = [index for index, contains_quote in enumerate(sentence_predictions)
                                           if contains_quote == 1]

    # Determining authors
    ne_is_cited = len(article_mentions) * [0]
    for quote_sentence_index in indices_sentences_containing_quotes:
        sentence_starts = [0] + [s_end + 1 for s_end in article_sentences][:-1]
        predicted_author_indices = attribute_quote_lazy(article_sentence_docs, quote_sentence_index, sentence_starts, sentence_in_quotes, cue_verbs)
        if len(predicted_author_indices) > 0:
            predicted_index_lazy = find_true_author_index(predicted_author_indices, article_mentions)
            if predicted_index_lazy > -1:
                ne_is_cited[predicted_index_lazy] = 1

    speakers = set()
    for i, label in enumerate(ne_is_cited):
        if label == 1:
            full_name = author_full_name_no_db(article_mentions, i)
            if full_name is not None and full_name not in speakers:
                speakers.add(full_name)

    predicted_experts = list(speakers)

    return predicted_experts
