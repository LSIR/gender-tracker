from spacy.tokens import Span


def is_substring(person, name):
    """
    Determines if name is a substring of person.

    :param person: string
        The complete string.
    :param name: string
        The string for which we want to know if it's a substring of person.
    :return: boolean
        True iff name is a subtring of person
    """
    person_tokens = person.split(' ')
    name_tokens = name.split(' ')
    for i in range(len(person_tokens)):
        j = 0
        while (i + j) < len(person_tokens) and j < len(name_tokens) and person_tokens[i + j] == name_tokens[j]:
            j = j + 1
        if j == len(name_tokens):
            return True
    return False


def find_full_name(all_people, name):
    """
    Determines if name is simply another mention of someone in all_people, or if it's the first mention of someone.

    :param all_people: list(string)
        The full name of everyone already seen in the document.
    :param name: string
        The mention of some person.
    :return:
        The full name of the person of it's another mention, or name if it's the first mention.
    """
    for person in all_people:
        if is_substring(person, name):
            return person
    return name


def correct_hyphen_errors(article):
    """
    Corrects an error that spaCy makes (seperates names that contain a hyphen into two named entities).

    :param article: spaCy.Doc
        The article in which to correct the entities.
    :return: list(spaCy.Span)
        The corrected entities.
    """
    entities = article.ents
    corrected_ents = []
    prev_per_ent = None
    for ent in entities:
        if ent.label_ == 'PER':
            if (prev_per_ent is not None) and \
                    (prev_per_ent.end_char == ent.start_char - 1) and \
                    (article.text[prev_per_ent.end_char] == '-'):
                # Create a new NE for the name with the hyphen
                merged_ent = Span(article, prev_per_ent.start, ent.end, label="PER")
                # Remove the last entity and add the new one.
                corrected_ents[-1] = merged_ent
            else:
                corrected_ents.append(ent)
            prev_per_ent = ent
        else:
            corrected_ents.append(ent)
            prev_per_ent = None
    return corrected_ents


def extract_person_mentions(paragraphs):
    """
    Finds all mentions of people in the article, and groups them into the same entity.

    :param paragraphs: list(spacy.doc)
        The list of documents for each paragraph in the article.
    :return: set(string), list(spaCy.Span), list(string)
        * A set containing the names of all people in the article
        * A list of all mentions of people in the article
        * A list of the full names of all people mentioned

    """
    # Correct entity splits on hyphens
    for p in paragraphs:
        p.ents = correct_hyphen_errors(p)

    # All mentions of people, containing the tuples (name, start_index, end_index)
    mentions_found = []
    start_index = 0
    for p in paragraphs:
        for ent in p.ents:
            if ent.label_ == 'PER':
                # -1 as ent.end is the first token after the mention
                mentions_found.append({
                    'name': ent.text,
                    'start': ent.start + start_index,
                    'end': ent.end + start_index - 1
                })
        start_index += len(p)

    # Sort from the longest name to the shortest
    mentions_found.sort(key=lambda x: -len(x['name'].split(' ')))
    # The set of people mentioned in the article (their full name)
    people = set()
    for mention in mentions_found:
        if mention['name'] not in people:
            full_name = find_full_name(people, mention['name'])
            mention['full_name'] = full_name
            if mention['name'] == full_name:
                people.add(mention['name'])
        else:
            mention['full_name'] = mention['name']

    return people, mentions_found
