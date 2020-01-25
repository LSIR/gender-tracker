

""" File containing helper methods to transform XML files to rows of a PostgreSQL database and vice versa. """


def overlap(seq1, seq2):
    """
    Determines if two sequences, given by their first and last element, overlap.

    :param seq1: (int, int)
        The first and last index of the first sequence.
    :param seq2: (int, int)
        The first and last index of the second sequence.
    :return: boolean.
        True if and only if seq1 and seq2 overlap.
    """
    return (seq1[0] <= seq2[0] <= seq1[1]) or (seq1[0] <= seq2[1] <= seq1[1])


def resolve_overlapping_people(author_indices):
    """
    Given a list of author indices, resolves indices that overlap so that they all start and end at the same token.
    Example:
        [[5], [7, 8], [], [7, 8, 9]] -> [[5], [7, 8, 9], [], [7, 8, 9]]
        [[5], [8], [], [7, 8, 9]] -> [[5], [7, 8, 9], [], [7, 8, 9]]
        [[5], [5, 6], [], [7, 8, 9]] -> [[5, 6], [5, 6], [], [7, 8, 9]]

    :param author_indices: list(list(int)).
        A list of indices of tokens that are authors of quotes
    :return: list(list(int))
        A list of lists of token indices that represent the same person.
    """
    expanded_indices = []
    for indices_1 in author_indices:
        if len(indices_1) > 0:
            min_first_token = indices_1[0]
            max_last_token = indices_1[-1]
            for indices_2 in author_indices:
                if len(indices_2) > 0:
                    start = indices_2[0]
                    end = indices_2[-1]
                    if overlap((start, end), (min_first_token, max_last_token)):
                        min_first_token = min(start, min_first_token)
                        max_last_token = max(end, max_last_token)
            expanded_indices.append(list(range(min_first_token, max_last_token + 1)))
        else:
            expanded_indices.append([])
    return expanded_indices
