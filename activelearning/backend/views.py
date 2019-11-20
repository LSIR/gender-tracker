from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .helpers import add_user_labels_to_db, request_labelling_task, form_sentence_json, form_paragraph_json,\
    parse_user_tags, load_paragraph_above
import json

# The life span of a cookie, in seconds
COOKIE_LIFE_SPAN = 1 * 60 * 60

# Default session ID (until the actual cookies are working)
USER_ID = 1111

# If in dev mode, don't touch the database:
DEV_MODE = True
LSIR_TAGGER = False


def load_content(request):
    """
    Selects either a sentence or a paragraph that needs to be labelled. Creates a JSON file that contains an article_id
    (int), a paragraph_id (int), a sentence_id ([int]), data (list[string]) and a task (either 'sentence' if a
    sentence needs to be labelled or 'paragraph' if a paragraph needs to be labelled).

    If a sentence needs to be labelled, sentence_id is a list of a least one integer, and data is a list of individual
    tokens (words). If a paragraph needs to be annotated, sentence_id is an empty list, and data is a list containing a
    single string, which is the content of the entire paragraph.

    :param request: The user request
    :return: Json A Json file containing the article_id, paragraph_id, sentence_id, data and task.
    """
    # Real Code
    # This needs to be the user's session cookie.
    user_id = manage_session_id(request)
    if not DEV_MODE:
        article, paragraph_id, sentence_id = request_labelling_task(user_id)
        if len(sentence_id) == 0:
            return JsonResponse(form_paragraph_json(article, paragraph_id))
        else:
            return JsonResponse(form_sentence_json(article, paragraph_id, sentence_id))
    else:
        # Placeholder as the database is empty.
        import random
        random_value = random.randint(1, 10)
        if random_value > 5:
            response = JsonResponse({
                'article_id': 2,
                'paragraph_id': 1,
                'sentence_id': [2],
                'data': ['Mais', '"', 'il', 'ne', 'pourra', 'plus', 'jamais', 'marcher', '"', ",",\
                         'selon', 'son', 'docteur', '.'],
                'task': 'sentence',
            })
        else:
            response = JsonResponse({
                'article_id': 3,
                'paragraph_id': 0,
                'sentence_id': [],
                'data': ['Les fractures de pied peuvent être très dangereuses, nous apprends le Dr. Jacques. L\''
                         'opération fût très compliquée. Elle s\'est bien passée. Mais "il ne pourra plus jamais'
                         ' marcher", selon son docteur.'],
                'task': 'paragraph',
            })
        return response


def load_rest_of_paragraph(request):
    """
    When the speaker of a quote wasn't in sentence reported speech, the user can ask to show the part of the
    paragraph that leads up to the quote.

    :param request: The user request.
    :return: Json A Json file containing the the list of tokens of the paragraph above the sentence.
    """
    # Session stuff
    user_id = manage_session_id(request)
    if not DEV_MODE:
        if request.method == 'GET':
            try:
                # Get user tags
                data = dict(request.GET)
                article_id = data['article_id']
                paragraph_id = data['paragraph_id']
                sentence_id = data['sentence_id']
                return JsonResponse(load_paragraph_above(article_id, paragraph_id, sentence_id))
            except KeyError:
                return HttpResponse('Failure. JSON parse failed.')
        return HttpResponse('Failure. Not a GET request.')
    else:
        if request.method == 'GET':
            try:
                # Get user tags
                data = dict(request.GET)
                print(f'Data: {data}')
                article_id = data['article_id']
                paragraph_id = data['paragraph_id']
                sentence_id = data['sentence_id']
                print(f'\nids: {article_id}, {paragraph_id}, {sentence_id}\n')
                text = {
                    'data': ['Les', 'fractures', 'de', 'pied', 'peuvent', 'être', 'très', 'dangereuses', 'nous',
                             'apprends', 'le', 'Dr.', 'Jacques', '.', 'L\'', 'opération', 'fût', 'très', 'compliquée',
                             '.', 'Elle', 's\'', 'est', 'bien', 'passée', '.']
                }
                return JsonResponse(text)
            except KeyError:
                return HttpResponse('Failure. JSON parse failed.')
        return HttpResponse('Failure. Not a GET request.')


@csrf_exempt
def submit_tags(request):
    # Session stuff
    user_id = manage_session_id(request)
    if request.method == 'POST':
        try:
            # Get user tags
            data = json.loads(request.body)
            article_id = data['article_id']
            paragraph_id = data['paragraph_id']
            sentence_id = data['sentence_id']
            tags = data['tags']
            authors = data['authors']

            if not DEV_MODE:
                sentence_labels, sentence_indices, author_indices = parse_user_tags(article_id, paragraph_id,
                                                                                    sentence_id,
                                                                                    tags, authors)
                for i in range(len(sentence_labels)):
                    add_user_labels_to_db(article_id, user_id, sentence_labels[i], sentence_indices[i], author_indices)
            else:
                print(f'\nSubmitted answers: user={user_id}, a={article_id}, p={paragraph_id}, s={sentence_id}, '
                      f'tags={tags}, authors={authors}\n')
            return HttpResponse('Success.')
        except KeyError:
            return HttpResponse('Failure. JSON parse failed.')
    return HttpResponse('Failure. Not a POST request.')


def manage_session_id(request):
    """
    Given a request, checks if the user already has a session id.
    If he doesn't, sets one that exipres one COOKIE_LIFE_SPAN later. 
    """
    # Clears cookies that have expired
    request.session.clear_expired()
    # If the user already doesn't have a session yet,
    # set a cookie that expires COOKIE_LIFE_SPAN hour later
    if not request.session.has_key('user'):
        # How to generate this?
        request.session['user'] = f'{USER_ID}'
        request.session.set_expiry(COOKIE_LIFE_SPAN)
    return request.session['user']
