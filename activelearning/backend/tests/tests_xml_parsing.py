from django.test import TestCase

import spacy

from backend.models import Article, UserLabel
from backend.xml_parsing.helpers import *
from backend.xml_parsing.postgre_to_xml import *
from backend.xml_parsing.xml_to_postgre import *
from backend.management.commands.addarticle import set_custom_boundaries


class HelperTestCase(TestCase):
    """ Test class for the helpers.py file in the xml_parsing package """

    def test_overlap_true(self):
        """ Checks that the method returns true for overlapping sequences """
        self.assertTrue(overlap([0, 0], [0, 0]))
        self.assertTrue(overlap([1, 1], [1, 1]))
        self.assertTrue(overlap([0, 1], [1, 1]))
        self.assertTrue(overlap([0, 2], [1, 1]))
        self.assertTrue(overlap([1, 2], [1, 1]))
        self.assertTrue(overlap([1, 1], [0, 1]))
        self.assertTrue(overlap([1, 1], [1, 2]))
        self.assertTrue(overlap([3, 5], [3, 5]))
        self.assertTrue(overlap([3, 5], [5, 7]))

    def test_overlap_false(self):
        """ Checks that the method returns true for overlapping sequences """
        self.assertFalse(overlap([0, 0], [1, 1]))
        self.assertFalse(overlap([1, 1], [0, 0]))
        self.assertFalse(overlap([0, 1], [2, 3]))
        self.assertFalse(overlap([0, 2], [3, 5]))
        self.assertFalse(overlap([2, 2], [1, 1]))
        self.assertFalse(overlap([0, 4], [8, 9]))
        self.assertFalse(overlap([4, 6], [1, 2]))
        self.assertFalse(overlap([3, 5], [6, 7]))
        self.assertFalse(overlap([6, 7], [3, 5]))

    def test_resolve_overlapping_people_1(self):
        """ Test that the method works correctly for no overlapping authors """
        authors = [[2], [], [4, 5]]
        resolved_authors = resolve_overlapping_people(authors)
        self.assertEquals(resolved_authors, authors)
        authors = [[], [], [4, 5]]
        resolved_authors = resolve_overlapping_people(authors)
        self.assertEquals(resolved_authors, authors)
        authors = [[2, 3], [], [4, 5]]
        resolved_authors = resolve_overlapping_people(authors)
        self.assertEquals(resolved_authors, authors)
        authors = [[1], [2], [3]]
        resolved_authors = resolve_overlapping_people(authors)
        self.assertEquals(resolved_authors, authors)

    def test_resolve_overlapping_people_2(self):
        """ Test that the method works correctly for overlapping authors """
        authors = [[2, 3], [2], [4, 5]]
        authors_clean = [[2, 3], [2, 3], [4, 5]]
        resolved_authors = resolve_overlapping_people(authors)
        self.assertEquals(resolved_authors, authors_clean)

        authors = [[2], [2, 3], [4, 5]]
        authors_clean = [[2, 3], [2, 3], [4, 5]]
        resolved_authors = resolve_overlapping_people(authors)
        self.assertEquals(resolved_authors, authors_clean)

        authors = [[2], [4, 5], [2, 3]]
        authors_clean = [[2, 3], [4, 5], [2, 3]]
        resolved_authors = resolve_overlapping_people(authors)
        self.assertEquals(resolved_authors, authors_clean)

        authors = [[2, 3], [], [1, 2, 3, 4], [4, 5]]
        authors_clean = [[1, 2, 3, 4, 5], [], [1, 2, 3, 4, 5], [1, 2, 3, 4, 5]]
        resolved_authors = resolve_overlapping_people(authors)
        self.assertEquals(resolved_authors, authors_clean)

        authors = [[1, 2], [2], [3]]
        authors_clean = [[1, 2], [1, 2], [3]]
        resolved_authors = resolve_overlapping_people(authors)
        self.assertEquals(resolved_authors, authors_clean)

        authors = [[1, 2, 3], [2], [3]]
        authors_clean = [[1, 2, 3], [1, 2, 3], [1, 2, 3]]
        resolved_authors = resolve_overlapping_people(authors)
        self.assertEquals(resolved_authors, authors_clean)


class PostgreToXMLTestCase(TestCase):
    """ Test class for the postgre_to_xml.py file in the xml_parsing package """

    def test_add_tags_to_tokens_1(self):
        """ Tests that the method works with no quote present """
        tokens = ['This', 'is', 'a', 'test', '.', 'I', 'hope', 'it', 'works', '.']
        labels = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
        authors = []
        returned_text = add_tags_to_tokens(tokens, labels, authors)
        self.assertEquals(returned_text, tokens)

    def test_add_tags_to_tokens_2(self):
        """ Tests that the method works with one author with a one-token name for a quote in the next sentence"""
        tokens = ['This', 'is', 'a', 'test', 'for', 'John', '.', 'He', 'said', 'go', 'outside', '.']
        annotated_tokens = ['This', 'is', 'a', 'test', 'for', '<author a="0">John</author>', '.',
                            'He', 'said', '<RS a="0">go', 'outside</RS>', '.']
        labels = [[0, 0, 0, 0, 0, 0, 0], [0, 0, 1, 1, 0]]
        authors = [[], [5]]
        returned_text = add_tags_to_tokens(tokens, labels, authors)
        self.assertEquals(returned_text, annotated_tokens)

    def test_add_tags_to_tokens_3(self):
        """ Tests that the method works with one author with a one-token name for a quote in the same sentence"""
        tokens = ['John', 'said', 'he', 'likes', 'to', 'eat', 'thai', 'food', '.']
        annotated_tokens = ['<author a="0">John</author>', 'said', 'he', '<RS a="0">likes', 'to', 'eat', 'thai',
                            'food</RS>', '.']
        labels = [[0, 0, 0, 1, 1, 1, 1, 1, 0]]
        authors = [[0]]
        returned_text = add_tags_to_tokens(tokens, labels, authors)
        self.assertEquals(returned_text, annotated_tokens)

    def test_add_tags_to_tokens_4(self):
        """ Tests that the method works with one author with a two-token name for a quote in the next sentence"""
        tokens = ['This', 'is', 'a', 'test', 'for', 'John', 'Smith', '.', 'He', 'said', 'go', 'outside', '.']
        annotated_tokens = ['This', 'is', 'a', 'test', 'for', '<author a="0">John', 'Smith</author>', '.',
                            'He', 'said', '<RS a="0">go', 'outside</RS>', '.']
        labels = [[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 1, 1, 0]]
        authors = [[], [5, 6]]
        returned_text = add_tags_to_tokens(tokens, labels, authors)
        self.assertEquals(returned_text, annotated_tokens)

    def test_add_tags_to_tokens_5(self):
        """ Tests that the method works with one author with a two-token name for a quote in the same sentence"""
        tokens = ['John', 'Smith', 'said', 'he', 'likes', 'to', 'eat', 'thai', 'food', '.']
        annotated_tokens = ['<author a="0">John', 'Smith</author>', 'said', 'he', '<RS a="0">likes',
                            'to', 'eat', 'thai', 'food</RS>', '.']
        labels = [[0, 0, 0, 0, 1, 1, 1, 1, 1, 0]]
        authors = [[0, 1]]
        returned_text = add_tags_to_tokens(tokens, labels, authors)
        self.assertEquals(returned_text, annotated_tokens)

    def test_add_tags_to_tokens_6(self):
        """ Tests that the method works with one author with a three-token name for a quote in the next sentence"""
        tokens = ['This', 'is', 'a', 'test', 'for', 'John', 'Henry', 'Smith', '.', 'He', 'said', 'go', 'outside', '.']
        annotated_tokens = ['This', 'is', 'a', 'test', 'for', '<author a="0">John', 'Henry', 'Smith</author>', '.',
                            'He', 'said', '<RS a="0">go', 'outside</RS>', '.']
        labels = [[0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 1, 1, 0]]
        authors = [[], [5, 6, 7]]
        returned_text = add_tags_to_tokens(tokens, labels, authors)
        self.assertEquals(returned_text, annotated_tokens)

    def test_add_tags_to_tokens_7(self):
        """ Tests that the method works with one author with a three-token name for a quote in the same sentence"""
        tokens = ['John', 'Henry', 'Smith', 'said', 'he', 'likes', 'to', 'eat', 'thai', 'food', '.']
        annotated_tokens = ['<author a="0">John', 'Henry', 'Smith</author>', 'said', 'he', '<RS a="0">likes',
                            'to', 'eat', 'thai', 'food</RS>', '.']
        labels = [[0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0]]
        authors = [[0, 1, 2]]
        returned_text = add_tags_to_tokens(tokens, labels, authors)
        self.assertEquals(returned_text, annotated_tokens)

    def test_add_tags_to_tokens_8(self):
        """ Tests that the method works with two authors"""
        tokens = ['This', 'is', 'a', 'test', 'for', 'John', 'Smith', 'and', 'James', '.', 'The',
                  'first', 'said', 'go', 'outside', '.', 'The', 'second', 'said', 'no', '.']
        annotated_tokens = ['This', 'is', 'a', 'test', 'for', '<author a="0">John', 'Smith</author>', 'and',
                            '<author a="1">James</author>', '.', 'The', 'first', 'said', '<RS a="0">go', 'outside</RS>',
                            '.', 'The', 'second', 'said', '<RS a="1">no</RS>', '.']
        labels = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 1, 1, 0], [0, 0, 0, 1, 0]]
        authors = [[], [5, 6], [8]]
        returned_text = add_tags_to_tokens(tokens, labels, authors)
        self.assertEquals(returned_text, annotated_tokens)

    def test_add_tags_to_tokens_9(self):
        """ Tests that the method works with three authors"""
        tokens = ['My', 'friend', 'John', 'hates', 'Mondays', '.',
                  'He', 'said', '"', 'I\'m', 'just', 'like', 'Garfield', '"', '.',
                  'Phil', 'Neville', 'told', 'him', 'he', 'loves', 'them', '.',
                  'That', 'made', 'him', 'say', '"', 'what', 'a', 'dumb', 'idea', '"', '.',
                  'Gary', 'told', 'them', 'he', 'hates', 'them', 'too', '.']
        annotated_tokens = \
            ['My', 'friend', '<author a="0">John</author>', 'hates', 'Mondays', '.',
             'He', 'said', '"', '<RS a="0">I\'m', 'just', 'like', 'Garfield</RS>', '"', '.',
             '<author a="1">Phil', 'Neville</author>', 'told', 'him', 'he', '<RS a="1">loves', 'them</RS>', '.',
             'That', 'made', 'him', 'say', '"', '<RS a="0">what', 'a', 'dumb', 'idea</RS>', '"', '.',
             '<author a="2">Gary</author>', 'told', 'them', 'he', '<RS a="2">hates', 'them', 'too</RS>', '.']
        labels = [
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 0]]
        authors = [[], [2], [15, 16], [2], [34]]
        returned_text = add_tags_to_tokens(tokens, labels, authors)
        self.assertEquals(returned_text, annotated_tokens)

    def test_database_to_xml_1(self):
        """ Tests that the method works with one paragraph """
        text = 'My friend John hates Mondays. He said "I\'m just like Garfield". Phil Neville told him he loves ' + \
               'them. That made him say "what a dumb idea". Gary told them he hates them too.'

        xml_text = '<?xml version="1.0"?>\n' \
                   '<article>\n' \
                   '\t<titre>Example article</titre>\n' \
                   '\t<p>My friend <author a="0">John </author>hates Mondays. He said "<RS a="0">I\'m just like ' \
                   'Garfield</RS>". <author a="1">Phil Neville </author>told him he <RS a="1">loves them</RS>. ' \
                   'That made him say "<RS a="0">what a dumb idea</RS>". <author a="2">Gary </author>told them he ' \
                   '<RS a="2">hates them too</RS>.</p>\n' \
                   '</article>'

        tokens = ['My ', 'friend ', 'John ', 'hates ', 'Mondays', '. ',
                  'He ', 'said ', '"', 'I\'m ', 'just ', 'like ', 'Garfield', '"', '. ',
                  'Phil ', 'Neville ', 'told ', 'him ', 'he ', 'loves ', 'them', '. ',
                  'That ', 'made ', 'him ', 'say ', '"', 'what ', 'a ', 'dumb ', 'idea', '"', '. ',
                  'Gary ', 'told ', 'them ', 'he ', 'hates ', 'them ', 'too', '.']

        labels = [
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 0]
        ]

        authors = [[], [2], [15, 16], [2], [34]]

        a = Article.objects.create(
            name='Example article',
            text=text,
            people={'people': ['John', 'Phil Neville', 'Gary']},
            tokens={'tokens': tokens},
            paragraphs={'paragraphs': [4]},
            sentences={'sentences': [5, 14, 22, 33, 41]},
            labeled={
                'labeled': [1, 1, 1, 1, 1],
                'fully_labeled': 1,
            },
            in_quotes={'in_quotes': []},
            confidence={
                'confidence': [0, 0, 0, 0, 0],
                'min_confidence': 0,
            },
            admin_article=False,
        )
        returned_text = database_to_xml(a, labels, authors)
        self.assertEquals(returned_text, xml_text)

    def test_database_to_xml_2(self):
        """ Tests that the method works with two paragraphs """
        text = 'My friend John hates Mondays. He said "I\'m just like Garfield". Phil Neville told him he loves ' + \
               'them. That made him say "what a dumb idea". Gary told them he hates them too.'

        xml_text = '<?xml version="1.0"?>\n' \
                   '<article>\n' \
                   '\t<titre>Example article</titre>\n' \
                   '\t<p>My friend <author a="0">John </author>hates Mondays. He said "<RS a="0">I\'m just like ' \
                   'Garfield</RS>". <author a="1">Phil Neville </author>told him he <RS a="1">loves them</RS>.</p>\n' \
                   '\t<p>That made him say "<RS a="0">what a dumb idea</RS>". <author a="2">Gary </author>told them ' \
                   'he <RS a="2">hates them too</RS>.</p>\n' \
                   '</article>'

        tokens = ['My ', 'friend ', 'John ', 'hates ', 'Mondays', '. ',
                  'He ', 'said ', '"', 'I\'m ', 'just ', 'like ', 'Garfield', '"', '. ',
                  'Phil ', 'Neville ', 'told ', 'him ', 'he ', 'loves ', 'them', '.',
                  'That ', 'made ', 'him ', 'say ', '"', 'what ', 'a ', 'dumb ', 'idea', '"', '. ',
                  'Gary ', 'told ', 'them ', 'he ', 'hates ', 'them ', 'too', '.']

        labels = [
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 0]
        ]

        authors = [[], [2], [15, 16], [2], [34]]

        a = Article.objects.create(
            name='Example article',
            text=text,
            people={'people': ['John', 'Phil Neville', 'Gary']},
            tokens={'tokens': tokens},
            paragraphs={'paragraphs': [2, 4]},
            sentences={'sentences': [5, 14, 22, 33, 41]},
            labeled={
                'labeled': [1, 1, 1, 1, 1],
                'fully_labeled': 1,
            },
            in_quotes={'in_quotes': []},
            confidence={
                'confidence': [0, 0, 0, 0, 0],
                'min_confidence': 0,
            },
            admin_article=False,
        )
        returned_text = database_to_xml(a, labels, authors)
        self.assertEquals(returned_text, xml_text)


class XMLToPostgreTestCase(TestCase):
    """ Test class for the postgre_to_xml.py file in the xml_parsing package """

    """ The loaded spaCy text model """
    nlp = spacy.load('fr_core_news_md')
    nlp.add_pipe(set_custom_boundaries, before="parser")

    def test_normalize_quotes_1(self):
        """ Tests that the method works with no quote present """
        text = 'This is a test that shoudln\'t change anything.'
        clean_text = normalize_quotes(text, default_quote='"', quotes=None)
        self.assertEquals(clean_text, text)

    def test_normalize_quotes_2(self):
        """ Tests that the method works with quotes present """
        text = 'This is a test that « should change » something.'
        normalized = 'This is a test that " should change " something.'
        clean_text = normalize_quotes(text, default_quote='"', quotes=None)
        self.assertEquals(clean_text, normalized)

    def test_process_article_1(self):
        """ Tests that the method a trivial article with one paragraph."""
        article_text = \
            '<?xml version="1.0"?>\n' \
            '<article>\n' \
            '\t<titre>Example article</titre>\n' \
            '\t<p>My friend Steven hates Mondays. He said "I\'m just like Garfield". Phil Neville told him he ' \
            'loves them. That made him say "what a dumb idea". Gary told them he hates them too.</p>\n' \
            '</article>'

        tokens = ['My ', 'friend ', 'Steven ', 'hates ', 'Mondays', '. ',
                  'He ', 'said ', '"', 'I\'', 'm ', 'just ', 'like ', 'Garfield', '"', '. ',
                  'Phil ', 'Neville ', 'told ', 'him ', 'he ', 'loves ', 'them', '.',
                  'That ', 'made ', 'him ', 'say ', '"', 'what ', 'a ', 'dumb ', 'idea', '"', '. ',
                  'Gary ', 'told ', 'them ', 'he ', 'hates ', 'them ', 'too', '.']

        in_quotes = [
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 1, 1, 1, 1, 1, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0
        ]

        parsed = process_article(article_text, self.nlp)
        self.assertEquals(parsed['name'], 'Example article')
        self.assertEquals(parsed['tokens'], tokens)
        self.assertEquals(parsed['p'], [4])
        self.assertEquals(parsed['s'], [5, 15, 23, 34, 42])
        self.assertEquals(parsed['people'], [(16, 18), (35, 36)])
        self.assertEquals(parsed['in_quotes'], in_quotes)

    def test_process_article_1(self):
        """ Tests that the method a trivial article with two paragraphs."""
        article_text = \
            '<?xml version="1.0"?>\n' \
            '<article>\n' \
            '\t<titre>Example article</titre>\n' \
            '\t<p>My friend Steven hates Mondays. He said "I\'m just like Garfield". Phil Neville told him he ' \
            'loves them.</p>\n' \
            '\t<p>That made him say "what a dumb idea". Gary told them he hates them too.</p>\n' \
            '</article>'

        tokens = ['My ', 'friend ', 'Steven ', 'hates ', 'Mondays', '. ',
                  'He ', 'said ', '"', 'I\'', 'm ', 'just ', 'like ', 'Garfield', '"', '. ',
                  'Phil ', 'Neville ', 'told ', 'him ', 'he ', 'loves ', 'them', '.',
                  'That ', 'made ', 'him ', 'say ', '"', 'what ', 'a ', 'dumb ', 'idea', '"', '. ',
                  'Gary ', 'told ', 'them ', 'he ', 'hates ', 'them ', 'too', '.']

        in_quotes = [
            0, 0, 0, 0, 0, 0,
            0, 0, 0, 1, 1, 1, 1, 1, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0
        ]

        parsed = process_article(article_text, self.nlp)
        self.assertEquals(parsed['name'], 'Example article')
        self.assertEquals(parsed['tokens'], tokens)
        self.assertEquals(parsed['p'], [2, 4])
        self.assertEquals(parsed['s'], [5, 15, 23, 34, 42])
        # Doesn't detect Steven. Hmmmmm
        self.assertEquals(parsed['people'], [(16, 18), (35, 36)])
        self.assertEquals(parsed['in_quotes'], in_quotes)
