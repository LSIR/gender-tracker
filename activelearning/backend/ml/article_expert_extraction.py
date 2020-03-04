from backend.ml.quote_attribution import predict_authors


def predict_article_experts(article_id, classifier, attribution_dataset, ovo):
    """
    Predicts the names of the experts cited in an article.

    :param article_id:
    :param classifier:
    :param attribution_dataset:
    :param ovo:
    :return:
    """
    people, mentions_found = None, None
    true_speakers, predicted_speakers = predict_authors(classifier, attribution_dataset, [article_id], ovo)

    return []
