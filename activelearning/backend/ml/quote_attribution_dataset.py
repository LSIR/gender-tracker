import numpy as np
from torch.utils.data import Dataset, DataLoader, Subset
from torch.utils.data.sampler import WeightedRandomSampler

from backend.ml.helpers import find_true_author_index
from backend.ml.quote_attribution_feature_extraction import *


def parse_article(article_dict, quote_dataset, extraction_method, cue_verbs, poly=None):
    """
    Creates feature vectors for each sentence in the article from the raw data.

    :param article_dict: dict
        A dict containing information about the fully labeled article. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
    :param quote_dataset: QuoteDetectionDataset
        The dataset for quote detection in which this article is contained.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param extraction_method: int
        The feature extraction method to use.
    :param poly: sklearn.preprocessing.PolynomialFeatures
        If defined, used for feature expansion.
    :return: list(np.array), list(int), int, int
        * The features for each (quote, speaker) pair in the article. The features for the i-th quote in the article
        and the j-th mention is at index [i * (num_mentions + 1) + j].
        * The label for each (quote, speaker) pair in the article. The label for the i-th quote in the article
        and the j-th mention is at index [i * (num_mentions + 1) + j].
        * The number of quotes in the article
        * The number of mentions in the article (num_mentions).
    """
    features = []
    labels = []
    mentions = article_dict['article'].people['mentions']
    for i, sent_index in enumerate(article_dict['quotes']):
        # List of indices of the tokens of the true author of the quote
        true_author = article_dict['authors'][i]
        true_mention_index = find_true_author_index(true_author, mentions)

        # Create features for all mentions in the article
        other_quotes = article_dict['quotes'][:i] + article_dict['quotes'][i + 1:]

        # The quote detection features for this sentence
        quote_features = quote_dataset.get_sentence_features(article_dict['article'].id, sent_index)

        for j, mention in enumerate(mentions):
            article = article_dict['article']
            sentences = article_dict['sentences']
            if extraction_method == 1:
                ne_features = attribution_features_1(article, sentences, sent_index, mention, cue_verbs)
            else:
                other_speakers = mentions[:j] + mentions[j+1:]
                ne_features = attribution_features_2(article, sentences, sent_index, mention, other_quotes,
                                                     other_speakers, cue_verbs)
            quote_mention_features = np.concatenate((quote_features, ne_features), axis=0)
            if poly:
                quote_mention_features = poly.fit_transform(quote_mention_features.reshape((-1, 1))).reshape((-1,))
            label = int(true_mention_index == j)
            features.append(quote_mention_features)
            labels.append(label)

        # Create weasel feature:
        weasel_feature = np.zeros(features[-1].shape[0])
        weasel_feature[:len(quote_features)] = quote_features
        label = int(true_mention_index == -1)
        features.append(weasel_feature)
        labels.append(label)

    return features, labels, len(article_dict['quotes']), len(mentions) + 1


def parse_article_ovo(article_dict, quote_dataset, extraction_method, cue_verbs, use_quote_features=False, poly=None):
    """
    Creates feature vectors for each sentence in the article from the raw data.

    :param article_dict: dict
        A dict containing information about the fully labeled article. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
    :param quote_dataset: QuoteDetectionDataset
        The dataset for quote detection in which this article is contained.
    :param extraction_method: int
        The index of the feature extraction method to use.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param use_quote_features: boolean
        Whether to add the features for quote detection of the sentence containing the quote to the dataset.
    :param poly: sklearn.preprocessing.PolynomialFeatures
        If defined, used for feature expansion.
    :return: list(np.array), list(int), int, int
        * The features for each (quote, speaker) pair in the article. The features for the i-th quote in the article
        and the j-th mention is at index [i * (num_mentions + 1) + j].
        * The label for each (quote, speaker) pair in the article. The label for the i-th quote in the article
        and the j-th mention is at index [i * (num_mentions + 1) + j].
        * The number of quotes in the article
        * The number of mentions in the article (num_mentions).
    """
    features = []
    labels = []
    mentions = article_dict['article'].people['mentions']
    mentions_with_weasel = mentions + [None]

    for i, sent_index in enumerate(article_dict['quotes']):
        # List of indices of the tokens of the true author of the quote
        true_author = article_dict['authors'][i]
        true_index = find_true_author_index(true_author, mentions)
        if true_index == -1:
            true_index = len(mentions)

        # Index of other quotes in the article
        other_quotes = article_dict['quotes'][:i] + article_dict['quotes'][i + 1:]
        
        # The quote detection features for this sentence
        quote_features = quote_dataset.get_sentence_features(article_dict['article'].id, sent_index)

        # Mention features for single mentions
        single_features = []
        for m in mentions_with_weasel:
            article = article_dict['article']
            s_docs = article_dict['sentences']
            if extraction_method == 1:
                single_features.append(attribution_features_ovo_1(article, s_docs, sent_index, m, cue_verbs))
            elif extraction_method == 2:
                single_features.append(attribution_features_ovo_2(article, s_docs, sent_index, m, cue_verbs))
            else:
                single_features.append(attribution_features_ovo_3(article, s_docs, sent_index, m, cue_verbs,
                                                                  other_quotes))

        for m1_index, f1 in enumerate(single_features):
            for m2_index, f2 in enumerate(single_features):
                if m1_index != m2_index:
                    m1_m2_features = np.concatenate((f1, f2), axis=0)
                    if use_quote_features:
                        m1_m2_features = np.concatenate((quote_features, m1_m2_features), axis=0)
                    if poly:
                        m1_m2_features = poly.fit_transform(m1_m2_features.reshape((-1, 1))).reshape((-1,))

                    if true_index == m1_index:
                        label = 0
                    elif true_index == m2_index:
                        label = 1
                    else:
                        # No good choice
                        label = 2
                    features.append(m1_m2_features)
                    labels.append(label)

    return features, labels, len(article_dict['quotes']), len(mentions_with_weasel)


class QuoteAttributionDataset(Dataset):
    """ Dataset comprised of labeled articles, with features extracted for quote attribution """

    def __init__(self, article_dicts, quote_dataset, cue_verbs, extraction_method, ovo=False, poly=None):
        """
        Initializes the dataset.

        :param article_dicts: list(dict)
        A dict containing information about the fully labeled article. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
        :param quote_dataset: QuoteDetectionDataset
            The dataset for quote detection in which this article is contained.
        :param cue_verbs: list(string)
            The list of all "cue verbs", which are verbs that often introduce reported speech.
        :param extraction_method: int
            The feature extraction method to use.
        :param ovo: boolean
            Whether or not to load one-vs-one features
        :param poly: sklearn.preprocessing.PolynomialFeatures
            If defined, used for feature expansion.
        """
        self.ovo = ovo
        self.features = []
        self.labels = []
        # Keys: article id, Values
        #   (first feature in the article,
        #    last feature in the article,
        #    number of quotes in the article,
        #    number of mentions in the article (including the weasel, which is the last one))
        self.article_features = {}

        for a_dict in article_dicts:
            if ovo:
                a_features, a_labels, a_quotes, a_mentions = parse_article_ovo(a_dict, quote_dataset, extraction_method,
                                                                               cue_verbs, poly=poly)
            else:
                a_features, a_labels, a_quotes, a_mentions = parse_article(a_dict, quote_dataset, extraction_method,
                                                                           cue_verbs)
            first_feature = len(self.features)
            self.features += a_features
            last_feature = len(self.features) - 1
            self.labels += a_labels
            self.article_features[a_dict['article'].id] = (first_feature, last_feature, a_quotes, a_mentions)

        self.feature_dimensionality = self.features[0].shape
        self.length = len(self.features)

    def __getitem__(self, index):
        """
        Finds the item at a given index of the dataset.

        :param index: int.
            The index at which we want the data.
        :return: np.array, np.array
            The features and label for the datapoint
        """
        return self.features[index], self.labels[index]

    def __len__(self):
        return self.length

    def get_article_indices(self, article_id):
        """
        Returns all indices of the dataset that contain features for a certain article

        :param article_id: int
            The unique id for which the features are wanted.
        :return: list(int)
            All indices containing features for this article
        """
        start, end, _, _ = self.article_features[article_id]
        return list(range(start, end + 1))

    def get_article_features(self, article_id):
        """
        Return all features for a given article.

        :param article_id: int
            The id of the article for which features are wanted.
        :return: int, int, int, int
            The first two values are the first and last index containing a feature for this article. The next two are
            the number of quotes and the number of potential speakers in the article.
        """
        return self.article_features[article_id]

    def get_quote_mention_features(self, article_id, quote_index):
        """
        Finds the features for a given sentence in an article.

        :param article_id: int
            The unique id of the article that contains the sentence.
        :param quote_index: int
            The index of the quote for which the features are needed in the article.
        :return: list(np.array), list(int)
            The features for the sentence and each mention, and their labels
        """
        a_start, _, num_quotes, num_mentions = self.article_features[article_id]
        if self.ovo:
            q_start = a_start + quote_index * num_mentions * (num_mentions - 1)
            next_q_start = a_start + (quote_index + 1) * num_mentions * (num_mentions - 1)
        else:
            q_start = a_start + quote_index * num_mentions
            next_q_start = q_start + num_mentions
        return self.features[q_start:next_q_start], self.labels[q_start:next_q_start]


def subset(dataset, article_indices):
    """
    Returns a subset of the dataset containing the features for only some articles.

    :param dataset: QuoteDetectionDataset
        The dataset from which to take a subset.
    :param article_indices: list(int)
        The indices of the articles to keep in the subset.
    :return:
    """
    indices = []
    for a_id in article_indices:
        indices += dataset.get_article_indices(a_id)
    return Subset(dataset, indices)


def subset_ovo(dataset, article_indices):
    """

    :param dataset:
    :param article_indices:
    :return:
    """
    indices = []
    for a_id in article_indices:
        for feature_index in dataset.get_article_indices(a_id):
            # Don't add feature vectors with no true label to the dataset.
            if dataset[feature_index][1] < 2:
                indices.append(feature_index)
    return Subset(dataset, indices)


def sampler_weights(dataset):
    """
    Computes the weights that need to be given to each index in the dataset for random sampling.

    :param dataset: Dataset
        The dataset to find the weights for
    :return: list(float), int
        The weights for each index in the dataset and the total number of samples in an epoch.
    """
    class_counts = [0, 0]
    for index in range(len(dataset)):
        _, label = dataset[index]
        class_counts[label] += 1

    divisor = 2 * class_counts[0] * class_counts[1]
    sample_weights = (class_counts[1] / divisor, class_counts[0] / divisor)
    weights = []
    for index in range(len(dataset)):
        _, label = dataset[index]
        weights.append(sample_weights[label])

    num_samples = 2 * min(class_counts[0], class_counts[1])
    return weights, num_samples


def sampler_weights_ovo(dataset):
    """
    Computes the weights that need to be given to each index in the dataset for random sampling.

    :param dataset: Dataset
        The dataset to find the weights for
    :return: list(float), int
        The weights for each index in the dataset and the total number of samples in an epoch.
    """
    # Class 0, 1, 2
    class_counts = [0, 0, 0]
    for index in range(len(dataset)):
        _, label = dataset[index]
        class_counts[label] += 1

    divisor = 2 * class_counts[0] * class_counts[1]
    sample_weights = (class_counts[1] / divisor, class_counts[0] / divisor)
    weights = []
    for index in range(len(dataset)):
        _, label = dataset[index]
        if label < 2:
            weights.append(sample_weights[label])
        else:
            weights.append(0)

    num_samples = 2 * min(class_counts[0], class_counts[1])
    return weights, num_samples


def attribution_loader(dataset, train=True, batch_size=None):
    """
    Creates a training set dataloader for a dataset. Uses a sampler to load the same number of datapoints from
    both classes.

    :param dataset: Dataset
        The dataset used from which to load data.
    :param train: boolean
        Whether to load a training or testing dataloader.
    :param batch_size: int.
        The batch size. The default is None, where the batch size is the size of the data.
    :return: torch.utils.data.DataLoader
        DataLoader for quote detection.
    """
    if batch_size is None:
        batch_size = len(dataset)
    if train:
        weights, num_samples = sampler_weights(dataset)
        sampler = WeightedRandomSampler(weights=weights, num_samples=num_samples, replacement=True)
        return DataLoader(dataset=dataset, batch_size=batch_size, sampler=sampler)
    else:
        return DataLoader(dataset=dataset, batch_size=batch_size, shuffle=False)
