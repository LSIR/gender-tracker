import numpy as np
from torch.utils.data import Dataset, DataLoader, Subset
from torch.utils.data.sampler import WeightedRandomSampler

from backend.ml.helpers import find_true_author_index


def extract_features(article, sentences, quote_index, speaker, other_quotes, cue_verbs):
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


def parse_article(article_dict, quote_dataset, cue_verbs, poly=None):
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
            ne_features = extract_features(article, sentences, sent_index, mention, other_quotes, cue_verbs)
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


def parse_article_ovo(article_dict, quote_dataset, cue_verbs, poly=None):
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
        true_index = find_true_author_index(true_author, mentions)

        # Create features for all mentions in the article
        other_quotes = article_dict['quotes'][:i] + article_dict['quotes'][i + 1:]

        # The quote detection features for this sentence
        quote_features = quote_dataset.get_sentence_features(article_dict['article'].id, sent_index)

        # Mention features for single mentions
        single_features = []
        for mention in mentions:
            article = article_dict['article']
            sentences = article_dict['sentences']
            single_features.append(extract_features(article, sentences, sent_index, mention, other_quotes, cue_verbs))

        # Create weasel feature:
        weasel_feature = np.zeros(single_features[-1].shape[0])
        single_features.append(weasel_feature)

        if true_index == -1:
            true_index = len(single_features) - 1

        for m1_index, f1 in enumerate(single_features):
            for m2_index, f2 in enumerate(single_features):
                if m1_index != m2_index:
                    quote_m1_m2_features = np.concatenate((quote_features, f1, f2), axis=0)
                    if poly:
                        quote_m1_m2_features = poly.fit_transform(quote_m1_m2_features.reshape((-1, 1))).reshape((-1,))

                    if true_index == m1_index:
                        label = 0
                    elif true_index == m2_index:
                        label = 1
                    else:
                        # No good choice
                        label = 2
                    features.append(quote_m1_m2_features)
                    labels.append(label)

    return features, labels, len(article_dict['quotes']), len(mentions) + 1


class QuoteAttributionDataset(Dataset):
    """ Dataset comprised of labeled articles, with features extracted for quote attribution """

    def __init__(self, article_dicts, quote_dataset, cue_verbs, ovo=False, poly=None):
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
        total_sentences = 0

        for a_dict in article_dicts:
            if ovo:
                a_features, a_labels, a_quotes, a_mentions = parse_article_ovo(a_dict, quote_dataset, cue_verbs, poly)
            else:
                a_features, a_labels, a_quotes, a_mentions = parse_article(a_dict, quote_dataset, cue_verbs, poly)
            self.features += a_features
            self.labels += a_labels
            self.article_features[a_dict['article'].id] = (total_sentences, total_sentences + len(a_labels) - 1,
                                                           a_quotes, a_mentions)
            total_sentences += len(a_labels)

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
