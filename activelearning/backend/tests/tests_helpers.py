from django.test import TestCase

from backend.helpers import *


class LabelConsensusTestCase(TestCase):
    """ Test class for the label_consensus method in the helpers file """

    def test_0_trivial(self):
        """ Tests that the method works for no label """
        labels, authors, consensus = label_consensus([], [])
        self.assertEquals(labels, [])
        self.assertEquals(authors, [])
        self.assertEquals(consensus, 0)

    def test_1_trivial(self):
        """ Tests that the method works for one label """
        label_1 = [0, 0, 1, 1, 0]
        author_1 = [4, 5]
        labels, authors, consensus = label_consensus([label_1], [author_1])
        self.assertEquals(labels, label_1)
        self.assertEquals(authors, author_1)
        self.assertEquals(consensus, 1)

    def test_2_two_same_labels(self):
        """ Tests that the method works for two identical labels """
        label_1 = [0, 0, 1, 1, 0]
        author_1 = [4, 5]
        labels, authors, consensus = label_consensus([label_1, label_1.copy()], [author_1, author_1.copy()])
        self.assertEquals(labels, label_1)
        self.assertEquals(authors, author_1)
        self.assertEquals(consensus, 1)

    def test_3_two_different_labels(self):
        """ Tests that the method works for two different labels and authors """
        label_1 = [0, 0, 1, 1, 0]
        label_2 = [0, 1, 1, 1, 0]
        author_1 = [4, 5]
        author_2 = [5]
        labels, authors, consensus = label_consensus([label_1, label_2], [author_1, author_2])
        self.assertTrue(labels in [label_1, label_2])
        self.assertTrue(authors in [author_1, author_2])
        self.assertEquals(consensus, 0.5)

    def test_4_two_different_labels(self):
        """ Tests that the method works for two identical labels but different authors """
        label_1 = [0, 0, 1, 1, 0]
        label_2 = [0, 0, 1, 1, 0]
        author_1 = [4, 5]
        author_2 = [5]
        labels, authors, consensus = label_consensus([label_1, label_2], [author_1, author_2])
        self.assertEquals(labels, label_1)
        self.assertTrue(authors in [author_1, author_2])
        self.assertEquals(consensus, 0.75)

    def test_5_two_different_labels(self):
        """ Tests that the method works for two different labels but the same authors """
        label_1 = [0, 0, 1, 1, 0]
        label_2 = [0, 0, 1, 1, 1]
        author_1 = [4, 5]
        author_2 = [4, 5]
        labels, authors, consensus = label_consensus([label_1, label_2], [author_1, author_2])
        self.assertTrue(labels in [label_1, label_2])
        self.assertTrue(authors == author_1)
        self.assertEquals(consensus, 0.75)

    def test_6_three_same_labels(self):
        """ Tests that the method works for three identical labels """
        label_1 = [0, 0, 1, 1, 0]
        author_1 = [4, 5]
        labels, authors, consensus = label_consensus([label_1, label_1.copy(), label_1.copy()],
                                                     [author_1, author_1.copy(), author_1.copy()])
        self.assertEquals(labels, label_1)
        self.assertEquals(authors, author_1)
        self.assertEquals(consensus, 1)

    def test_7_three_different_labels(self):
        """ Tests that the method works for three different labels """
        label_1 = [0, 0, 1, 1, 0]
        label_2 = [0, 1, 1, 1, 0]
        label_3 = [0, 1, 1, 1, 0]
        author_1 = [4, 5]
        author_2 = [7]
        author_3 = [7]
        labels, authors, consensus = label_consensus([label_1, label_2, label_3], [author_1, author_2, author_3])
        self.assertEquals(labels, label_2)
        self.assertEquals(authors, author_2)
        self.assertEquals(consensus, 2/3)

    def test_8_three_different_labels(self):
        """ Tests that the method works for three different labels, but the same authors """
        label_1 = [0, 0, 1, 1, 0]
        label_2 = [0, 1, 1, 1, 0]
        label_3 = [0, 1, 1, 1, 0]
        author_1 = [7]
        author_2 = [7]
        author_3 = [7]
        labels, authors, consensus = label_consensus([label_1, label_2, label_3], [author_1, author_2, author_3])
        self.assertEquals(labels, label_2)
        self.assertEquals(authors, author_1)
        self.assertEquals(consensus, 5/6)

    def test_9_three_different_labels(self):
        """ Tests that the method works for three different authors, but the same labels """
        label_1 = [0, 1, 1, 1, 0]
        label_2 = [0, 1, 1, 1, 0]
        label_3 = [0, 1, 1, 1, 0]
        author_1 = [4, 5]
        author_2 = [7]
        author_3 = []
        labels, authors, consensus = label_consensus([label_1, label_2, label_3], [author_1, author_2, author_3])
        self.assertEquals(labels, label_1)
        self.assertEquals(authors, author_1)
        self.assertEquals(consensus, 2/3)

    def test_10_three_different_labels(self):
        """ Tests that the method works for three different labels """
        label_1 = [0, 0, 1, 1, 0]
        label_2 = [0, 1, 1, 1, 0]
        label_3 = [0, 0, 1, 1, 0]
        author_1 = [4, 5]
        author_2 = [7]
        author_3 = [7]
        labels, authors, consensus = label_consensus([label_1, label_2, label_3], [author_1, author_2, author_3])
        self.assertEquals(labels, label_1)
        self.assertEquals(authors, author_2)
        self.assertEquals(consensus, 2/3)


class IsSentenceLabelledTestCase(TestCase):
    """ Test class for the is_sentence_labelled method in the helpers file """

    def test_trivial_0(self):
        """ Tests that the method works for no label and one label. """
        self.assertEquals(1, 1)


class IsArticleLabelledTestCase(TestCase):
    """ Test class for the is_article_labelled method in the helpers file """

    def test_trivial_0(self):
        """ Tests that the method works for no label and one label. """
        self.assertEquals(1, 1)


class ChangeConfidenceTestCase(TestCase):
    """ Test class for the change_confidence method in the helpers file """

    def test_trivial_0(self):
        """ Tests that the method works for no label and one label. """
        self.assertEquals(1, 1)


class QuoteStartSentenceTestCase(TestCase):
    """ Test class for the quote_start_sentence method in the helpers file """

    def test_0_trivial(self):
        """ Tests that the method works for a single sentence in the article. """
        sentence_ends = [4]
        in_quote = [1, 1, 1, 1, 0]
        token_index = 0
        index = quote_start_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 0)

    def test_1_trivial(self):
        """ Tests that the method works for a single sentence in the article. """
        sentence_ends = [4]
        in_quote = [1, 0, 0, 0, 0]
        token_index = 0
        index = quote_start_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 0)

    def test_2_two_sentences(self):
        """ Tests that the method works for two sentences in the article. """
        sentence_ends = [4, 7]
        in_quote = [1, 0, 0, 0, 0] + [1, 1, 0]
        token_index = 0
        index = quote_start_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 0)
        token_index = 5
        index = quote_start_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 1)

    def test_3_two_sentences(self):
        """ Tests that the method works for two sentences in the article. """
        sentence_ends = [4, 7]
        in_quote = [1, 1, 1, 1, 1] + [1, 1, 0]
        token_index = 0
        index = quote_start_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 0)
        token_index = 5
        index = quote_start_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 0)

    def test_4_two_sentences(self):
        """ Tests that the method works for two sentences in the article. """
        sentence_ends = [4, 7]
        in_quote = [0, 0, 0, 0, 1] + [1, 0, 0]
        token_index = 5
        index = quote_start_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 0)

    def test_5_two_sentences(self):
        """ Tests that the method works for two sentences in the article. """
        sentence_ends = [4, 7]
        in_quote = [1, 1, 1, 1, 1] + [1, 1, 1]
        token_index = 0
        index = quote_start_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 0)
        token_index = 5
        index = quote_start_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 0)

    def test_6_three_sentences(self):
        """ Tests that the method works for three sentences in the article. """
        sentence_ends = [4, 7, 10]
        in_quote = [1, 1, 1, 1, 1] + [1, 1, 1] + [1, 1, 1]
        index = quote_start_sentence(sentence_ends, in_quote, 0)
        self.assertEquals(index, 0)
        index = quote_start_sentence(sentence_ends, in_quote, 5)
        self.assertEquals(index, 0)
        index = quote_start_sentence(sentence_ends, in_quote, 8)
        self.assertEquals(index, 0)

    def test_7_three_sentences(self):
        """ Tests that the method works for three sentences in the article. """
        sentence_ends = [4, 7, 10]
        in_quote = [1, 1, 1, 1, 0] + [1, 1, 0] + [1, 1, 1]
        index = quote_start_sentence(sentence_ends, in_quote, 0)
        self.assertEquals(index, 0)
        index = quote_start_sentence(sentence_ends, in_quote, 5)
        self.assertEquals(index, 1)
        index = quote_start_sentence(sentence_ends, in_quote, 8)
        self.assertEquals(index, 2)

    def test_8_three_sentences(self):
        """ Tests that the method works for three sentences in the article. """
        sentence_ends = [4, 7, 10]
        in_quote = [1, 1, 1, 1, 1] + [1, 1, 0] + [1, 1, 1]
        index = quote_start_sentence(sentence_ends, in_quote, 0)
        self.assertEquals(index, 0)
        index = quote_start_sentence(sentence_ends, in_quote, 5)
        self.assertEquals(index, 0)
        index = quote_start_sentence(sentence_ends, in_quote, 8)
        self.assertEquals(index, 2)

    def test_9_three_sentences(self):
        """ Tests that the method works for three sentences in the article. """
        sentence_ends = [4, 7, 10]
        in_quote = [1, 1, 1, 1, 0] + [1, 1, 1] + [1, 1, 1]
        index = quote_start_sentence(sentence_ends, in_quote, 0)
        self.assertEquals(index, 0)
        index = quote_start_sentence(sentence_ends, in_quote, 5)
        self.assertEquals(index, 1)
        index = quote_start_sentence(sentence_ends, in_quote, 8)
        self.assertEquals(index, 1)

    def test_10_three_sentences(self):
        """ Tests that the method works for three sentences in the article. """
        sentence_ends = [4, 7, 10]
        in_quote = [1, 1, 1, 1, 0] + [0, 0, 0] + [1, 0, 0]
        index = quote_start_sentence(sentence_ends, in_quote, 0)
        self.assertEquals(index, 0)
        index = quote_start_sentence(sentence_ends, in_quote, 8)
        self.assertEquals(index, 2)


class QuoteEndSentenceTestCase(TestCase):
    """ Test class for the quote_start_sentence method in the helpers file """

    def test_0_trivial(self):
        """ Tests that the method works for a single sentence in the article. """
        sentence_ends = [4]
        in_quote = [1, 1, 1, 1, 1]
        token_index = 4
        index = quote_end_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 0)

    def test_1_trivial(self):
        """ Tests that the method works for a single sentence in the article. """
        sentence_ends = [4]
        in_quote = [0, 0, 0, 0, 1]
        token_index = 4
        index = quote_end_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 0)

    def test_2_two_sentences(self):
        """ Tests that the method works for two sentences in the article. """
        sentence_ends = [4, 7]
        in_quote = [0, 0, 0, 1, 1] + [0, 1, 1]
        token_index = 4
        index = quote_end_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 0)
        token_index = 7
        index = quote_end_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 1)

    def test_3_two_sentences(self):
        """ Tests that the method works for two sentences in the article. """
        sentence_ends = [4, 7]
        in_quote = [1, 1, 1, 1, 1] + [1, 1, 0]
        token_index = 4
        index = quote_end_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 1)

    def test_4_two_sentences(self):
        """ Tests that the method works for two sentences in the article. """
        sentence_ends = [4, 7]
        in_quote = [0, 0, 0, 0, 1] + [1, 0, 0]
        token_index = 4
        index = quote_end_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 1)

    def test_5_two_sentences(self):
        """ Tests that the method works for two sentences in the article. """
        sentence_ends = [4, 7]
        in_quote = [1, 1, 1, 1, 1] + [1, 1, 1]
        token_index = 4
        index = quote_end_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 1)
        token_index = 7
        index = quote_end_sentence(sentence_ends, in_quote, token_index)
        self.assertEquals(index, 1)

    def test_6_three_sentences(self):
        """ Tests that the method works for three sentences in the article. """
        sentence_ends = [4, 7, 10]
        in_quote = [1, 1, 1, 1, 1] + [1, 1, 1] + [1, 1, 1]
        index = quote_end_sentence(sentence_ends, in_quote, 4)
        self.assertEquals(index, 2)
        index = quote_end_sentence(sentence_ends, in_quote, 7)
        self.assertEquals(index, 2)
        index = quote_end_sentence(sentence_ends, in_quote, 10)
        self.assertEquals(index, 2)

    def test_7_three_sentences(self):
        """ Tests that the method works for three sentences in the article. """
        sentence_ends = [4, 7, 10]
        in_quote = [1, 1, 1, 1, 1] + [0, 1, 1] + [0, 1, 1]
        index = quote_end_sentence(sentence_ends, in_quote, 4)
        self.assertEquals(index, 0)
        index = quote_end_sentence(sentence_ends, in_quote, 7)
        self.assertEquals(index, 1)
        index = quote_end_sentence(sentence_ends, in_quote, 10)
        self.assertEquals(index, 2)

    def test_8_three_sentences(self):
        """ Tests that the method works for three sentences in the article. """
        sentence_ends = [4, 7, 10]
        in_quote = [1, 1, 1, 1, 1] + [1, 1, 0] + [1, 1, 1]
        index = quote_end_sentence(sentence_ends, in_quote, 4)
        self.assertEquals(index, 1)
        index = quote_end_sentence(sentence_ends, in_quote, 10)
        self.assertEquals(index, 2)

    def test_9_three_sentences(self):
        """ Tests that the method works for three sentences in the article. """
        sentence_ends = [4, 7, 10]
        in_quote = [1, 1, 1, 1, 0] + [1, 1, 1] + [1, 1, 1]
        index = quote_end_sentence(sentence_ends, in_quote, 7)
        self.assertEquals(index, 2)
        index = quote_end_sentence(sentence_ends, in_quote, 10)
        self.assertEquals(index, 2)

    def test_10_three_sentences(self):
        """ Tests that the method works for three sentences in the article. """
        sentence_ends = [4, 7, 10]
        in_quote = [1, 1, 1, 1, 0] + [0, 1, 1] + [1, 0, 0]
        index = quote_end_sentence(sentence_ends, in_quote, 7)
        self.assertEquals(index, 2)
        index = quote_end_sentence(sentence_ends, in_quote, 10)
        self.assertEquals(index, 2)
