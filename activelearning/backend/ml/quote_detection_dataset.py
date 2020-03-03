import numpy as np
from torch.utils.data import Dataset, DataLoader, Subset
from torch.utils.data.sampler import WeightedRandomSampler

from backend.helpers import aggregate_label


def feature_extraction(sentence, cue_verbs, in_quotes):
    """
    Gets features for possible elements in the sentence that can hint to it having a quote:

    :param sentence: spaCy.doc.
        The sentence to extract features from.
    :param cue_verbs: list(string).
        The sentence to extract features from.
    :param in_quotes: list(int).
        Whether each token in the sentence is between quotes or not
    :return: np.array
        The features extracted.
    """
    sentence_length = len(sentence)
    contains_quote = int('"' in sentence.text)
    tokens_inside_quote = sum(in_quotes)
    contains_named_entity = int(len(sentence.ents) > 0)
    contains_per_named_entity = int(len([ne for ne in sentence.ents if ne.label_ == 'PER']) > 0)
    sentence_inside_quotes = int(len(in_quotes) == sum(in_quotes))
    inside_quote_proportion = sum(in_quotes)/len(in_quotes)

    def contains_cue_verb():
        for token in sentence:
            if token.lemma_ in cue_verbs:
                return 1
        return 0

    def contains_pronoun():
        for token in sentence:
            if token.pos_ == 'PRON':
                return 1
        return 0

    def contains_parataxis():
        for token in sentence:
            if token.dep_ == 'parataxis':
                return 1
        return 0

    def number_of_verbs():
        verbs = 0
        for token in sentence:
            if token.pos_ == 'VERB':
                verbs += 1
        return verbs

    def verb_inside_quotes():
        for index, token in enumerate(sentence):
            if token.pos_ == 'VERB' and in_quotes[index] == 1:
                return 1
        return 0

    def contains_selon():
        for token in sentence:
            if token.text.lower() == 'selon':
                return True
        return False

    return np.array([
        sentence_length,
        contains_quote,
        tokens_inside_quote,
        contains_named_entity,
        contains_per_named_entity,
        contains_cue_verb(),
        contains_pronoun(),
        contains_parataxis(),
        number_of_verbs(),
        verb_inside_quotes(),
        sentence_inside_quotes,
        inside_quote_proportion,
        contains_selon(),
    ])


def parse_article(article, sentences, cue_verbs, poly=None):
    """
    Creates feature vectors for each sentence in the article from the raw data.

    :param article: models.Article
        A fully labeled article for which to create features.
    :param sentences: list(spaCy.Doc)
        the spaCy.Doc for each sentence in the article.
    :param cue_verbs: list(string)
        The list of all "cue verbs", which are verbs that often introduce reported speech.
    :param poly: sklearn.preprocessing.PolynomialFeatures
        If defined, used for feature expansion.
    """
    article_features = []
    article_labels = []
    sentence_start = 0
    for sentence_index, end in enumerate(article.sentences['sentences']):
        # Compute sentence features
        sentence = sentences[sentence_index]
        in_quotes = article.in_quotes['in_quotes'][sentence_start:end + 1]
        features = feature_extraction(sentence, cue_verbs, in_quotes)
        if poly:
            features = poly.fit_transform(features.reshape((-1, 1))).reshape((-1,))
        # Compute sentence label
        sentence_labels, sentence_authors, _ = aggregate_label(article, sentence_index)
        label = int(sum(sentence_labels) > 0)
        # Adds the sentence and label to the dataset
        article_features.append(features)
        article_labels.append(label)
        sentence_start = end + 1

    return article_features, article_labels


class QuoteDetectionDataset(Dataset):
    """ Dataset comprised of labeled articles """

    def __init__(self, articles, sentences, cue_verbs, poly=None):
        """
        Initializes the dataset.

        :param articles: list(models.Article)
            A list of fully labeled articles to add to the dataset.
        :param sentences: list(list(spaCy.Doc))
            the spaCy.Doc for each sentence in each article.
        :param cue_verbs: list(string)
            The list of all "cue verbs", which are verbs that often introduce reported speech.
        :param poly: sklearn.preprocessing.PolynomialFeatures
            If defined, used for feature expansion.
        """
        self.features = []
        self.labels = []
        self.article_features = {}
        total_sentences = 0

        for index, article in enumerate(articles):
            article_features, article_labels = parse_article(article, sentences[index], cue_verbs, poly)
            self.features += article_features
            self.labels += article_labels
            self.article_features[article.id] = (total_sentences, total_sentences + len(article_labels) - 1)
            total_sentences += len(article_labels)

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
        start, end = self.article_features[article_id]
        return list(range(start, end + 1))

    def get_sentence_features(self, article_id, sentence_index):
        """
        Finds the features for a given sentence in an article.

        :param article_id: int
            The unique id of the article that contains the sentence.
        :param sentence_index: int
            The index of the sentence for which the features are needed in the article.
        :return: np.array
            The features for the sentence.
        """
        return self.features[self.article_features[article_id][0] + sentence_index]


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


def detection_loader(dataset, train=True, batch_size=None):
    """
    Creates a training set dataloader for a dataset. Uses a sampler to load the same number of datapoints from
    both classes. The dataloader returns shuffled data, as a sampler is used to balance the classes (on average, half
    the samples seen will be quotes and the other half won't be).

    :param dataset: QuoteDetectionDataset
        The dataset used from which to load data
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
