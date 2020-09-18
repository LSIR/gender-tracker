from torch.utils.data import Dataset, DataLoader, Subset
from torch.utils.data.sampler import WeightedRandomSampler

from backend.ml.helpers import find_true_author_index
from backend.ml.author_prediction_feature_extraction import *


def parse_article(article_dict, cue_verbs, poly=None):
    """
    Creates feature vectors for each sentence in the article from the raw data.

    :param article_dict: dict
        A dict containing information about the fully labeled article. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param poly: sklearn.preprocessing.PolynomialFeatures
        If defined, used for feature expansion.
    :return: list(np.array), list(int), int, int
        * The features for each speaker in the article. The features for the i-th speaker in the article is at index i.
        * The label for each speaker in the article. The label for the i-th speaker in the article is at index i.
        * The number of speakers in the article
    """
    features = []
    speakers_in_article = article_dict['article'].people['mentions']

    for i, speaker in enumerate(speakers_in_article):
        speaker_features = attribution_features_baseline(
            article_dict['article'],
            article_dict['sentences'],
            article_dict['quotes'],
            speaker,
            speakers_in_article[:i] + speakers_in_article[i + 1:],
            cue_verbs
        )
        if poly:
            speaker_features = poly.fit_transform(speaker_features.reshape((-1, 1))).reshape((-1,))
        features.append(
            speaker_features
        )

    labels = len(speakers_in_article) * [0]

    # Set labels by looking at which quote belongs to which speaker
    for i, sent_index in enumerate(article_dict['quotes']):
        # List of indices of the tokens of the true author of the quote
        true_author = article_dict['authors'][i]
        true_mention_index = find_true_author_index(true_author, speakers_in_article)
        if true_mention_index >= 0:
            labels[true_mention_index] = 1

    return features, labels, len(speakers_in_article)


class AuthorPredictionDataset(Dataset):
    """ Dataset comprised of labeled articles, with features extracted for quote attribution """

    def __init__(self, article_dicts, cue_verbs, poly=None):
        """
        Initializes the dataset.

        :param article_dicts: list(dict)
        A dict containing information about the fully labeled article. Keys:
            * 'article': models.Article, the article containing the quote
            * 'quotes': list(int), the indices of sentences that contain quotes in the article.
            * 'author': list(list(int)), the indices of the tokens of the author for each quote.
        :param cue_verbs: list(string)
            The list of all "cue verbs", which are verbs that often introduce reported speech.
        :param poly: sklearn.preprocessing.PolynomialFeatures
            If defined, used for feature expansion.
        """
        self.features = []
        self.labels = []

        # Keys: article id
        # Values: first feature in the article
        #         last feature in the article
        #         number of speakers in the article
        self.article_features = {}

        for a_dict in article_dicts:
            article_features, article_labels, article_speakers = parse_article(a_dict, cue_verbs, poly=poly)
            first_feature = len(self.features)
            self.features += article_features
            last_feature = len(self.features) - 1
            self.labels += article_labels
            self.article_features[a_dict['article'].id] = (first_feature, last_feature, article_speakers)

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
        start, end, _ = self.article_features[article_id]
        return list(range(start, end + 1))

    def get_article_features(self, article_id):
        """
        Return all features for a given article.

        :param article_id: int
            The id of the article for which features are wanted.
        :return: int, int, int
            The first two values are the first and last index containing a feature for this article. The last one is the
            number of potential quote authors in the article.
        """
        return self.article_features[article_id]


def subset(dataset, article_indices):
    """
    Returns a subset of the dataset containing the features for only some articles.

    :param dataset: AuthorPredictionDataset
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


def author_prediction_loader(dataset, train=True, batch_size=None):
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
