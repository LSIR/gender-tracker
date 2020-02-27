import numpy as np
from torch.utils.data import Dataset, DataLoader, Subset
from torch.utils.data.sampler import WeightedRandomSampler

from backend.ml.helpers import find_true_author_index


def extract_features(article, quote_index, speaker, other_quotes, nlp, cue_verbs):
    """
    Gets the features for speaker attribution for a single speaker, in the one vs one case. The following features are
    taken, for a quote q and a speaker s where q.sent is the index of the sentence containing the quote, s.start is the
    index of the first token of the speaker s, s.end of the last, and s.sent is the index.

    :param article: models.Article
        The article from which the quote and speakers are taken.
    :param quote_index: int
        The index of the sentence containing a quote in the article.
    :param speaker: dict.
        The speaker. Has keys 'name', 'full_name', 'start', 'end', as described in the database.
    :param other_quotes: list(int)
        The index of other sentences containing quotes in the article.
    :param nlp: spaCy.Language
        The language model used to tokenize the text
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :return: np.array
        The features extracted
    """
    s_sent = 0
    while s_sent < len(article.sentences['sentences']) and article.sentences['sentences'][s_sent] < speaker['end']:
        s_sent = s_sent + 1

    s_par = 0
    while s_par < len(article.paragraphs['paragraphs']) and article.paragraphs['paragraphs'][s_par] < s_sent:
        s_par = s_par + 1

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
            if 0 < quote_index - other_q <= 5:
                quotes_above += 1
        return quotes_above

    speaker_in_quotes = article.in_quotes['in_quotes'][speaker['end']]

    def speaker_with_cue_verb():
        sentence_start = 0
        if s_sent > 0:
            sentence_start = article.sentences['sentences'][s_sent - 1] + 1
        sentence_end = article.sentences['sentences'][s_sent]
        tokens = nlp(''.join(article.tokens['tokens'][sentence_start:sentence_end + 1]))
        for token in tokens:
            if token.lemma_ in cue_verbs:
                return True
        return False

    return np.array([
        sentence_dist,
        paragraph_dist,
        separating_quotes(),
        quotes_above_q(),
        speaker_in_quotes,
        speaker_with_cue_verb(),
    ])


def parse_article(article_dict, quote_dataset, nlp, cue_verbs, poly=None):
    """
    Creates feature vectors for each sentence in the article from the raw data.

    :param article_dict: dict
        A dict containing information about the fully labeled article. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
    :param quote_dataset: QuoteDetectionDataset
        The dataset for quote detection in which this article is contained.
    :param nlp: spaCy.Language
        The language model used to tokenize the text
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
            ne_features = extract_features(article_dict['article'], sent_index, mention, other_quotes, nlp, cue_verbs)
            quote_mention_features = np.concatenate((quote_features, ne_features), axis=0)
            if poly:
                quote_mention_features = poly.fit_transform(quote_mention_features)
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


class QuoteAttributionDataset(Dataset):
    """ Dataset comprised of labeled articles, with features extracted for quote attribution """

    def __init__(self, article_dicts, quote_dataset, nlp, cue_verbs, poly=None):
        """
        Initializes the dataset.

        :param article_dicts: list(dict)
        A dict containing information about the fully labeled article. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
        :param quote_dataset: QuoteDetectionDataset
            The dataset for quote detection in which this article is contained.
        :param nlp: spaCy.Language
            The language model used to tokenize the text
        :param cue_verbs: list(string)
            The list of all "cue verbs", which are verbs that often introduce reported speech.
        :param poly: sklearn.preprocessing.PolynomialFeatures
            If defined, used for feature expansion.
        """
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
            a_features, a_labels, a_quotes, a_mentions = parse_article(a_dict, quote_dataset, nlp, cue_verbs, poly)
            self.features += a_features
            self.labels += a_labels
            self.article_features[a_dict['article'].id] = (total_sentences, total_sentences + len(a_labels) - 1,
                                                           a_quotes, a_mentions)
            total_sentences += len(a_labels)

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


def attribution_train_loader(dataset, batch_size=1):
    """
    Creates a training set dataloader for a dataset. Uses a sampler to load the same number of datapoints from
    both classes.

    :param dataset: Dataset
        The dataset used from which to load data.
    :param batch_size: int.
        The batch size for training.
    :return: torch.utils.data.DataLoader
        DataLoader for quote detection.
    """
    weights, num_samples = sampler_weights(dataset)
    sampler = WeightedRandomSampler(weights=weights, num_samples=num_samples, replacement=True)
    data_loader = DataLoader(dataset=dataset, batch_size=batch_size, sampler=sampler)
    return data_loader


def attribution_test_loader(dataset, batch_size=None):
    """
    Creates a training set dataloader for a dataset. Does balance the two classes

    :param dataset: Dataset
        The dataset used from which to load data.
    :param batch_size: int.
        The batch size for training. If none, the whole test dataset is returned at once.
    :return: torch.utils.data.DataLoader
        DataLoader for quote detection.
    """
    if batch_size is None:
        batch_size = len(dataset)
    data_loader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=False)
    return data_loader
