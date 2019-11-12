from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .helpers import load_article, parse_xml, request_labelling_task, form_sentence_json, form_paragraph_json
import json

# The life span of a cookie, in seconds
COOKIE_LIFE_SPAN = 1 * 60 * 60

# Default session ID (until the actual cookies are working)
USER_ID = 1111


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
    """
    # This needs to be the user's session cookie.
    session_id = 1234
    article, paragraph_id, sentence_id = request_labelling_task(session_id)
    if len(sentence_id) == 0:
        return JsonResponse(form_paragraph_json(article, paragraph_id))
    else:
        return JsonResponse(form_sentence_json(article, paragraph_id, sentence_id))
    """
    # Session stuff
    user_id = manage_session_id(request)
    # Placeholder as the database is empty.
    import random
    random_value = random.randint(1, 10)
    if random_value > 5:
        response = JsonResponse({
            'article_id': 2,
            'paragraph_id': 1,
            'sentence_id': [2],
            'data': ['Le', 'thé', 'est', 'bon', 'pour', 'la', 'santé', '.'],
            'task': 'sentence',
        })
    else:
        response = JsonResponse({
            'article_id': 3,
            'paragraph_id': 0,
            'sentence_id': [],
            'data': ['Le thé est très bon pour la santé. Mais il faut en boire en petite quantité.'
                     'Il contient tout de même de la caféine.'],
            'task': 'paragraph',
        })
    return response


@csrf_exempt
def submit_tags(request):
    # Session stuff
    user_id = manage_session_id(request)
    if request.method == 'POST':
        try:
            # Get user tags
            data = json.loads(request.body)
            tags = data['tags']
            print(tags)
            return HttpResponse('Success.')
        except KeyError:
            print('error')
            return HttpResponse('Failiure. JSON parse failed.')
    return HttpResponse('Failiure. Not a POST request.')


def manage_session_id(request):
    """
    Given a request, checks if the user already has a session id.
    If he doesn't, sets one that exipres one COOKIE_LIFE_SPAN later. 
    """
    # Get user session id. If he has none, set one.
    print('\nReceived request')
    # Clears cookies that have expired
    request.session.clear_expired()
    # If the user already doesn't have a session yet,
    # set a cookie that expires COOKIE_LIFE_SPAN hour later
    if request.session.has_key('user'):
        print('Returning user:', request.session['user'])
        print('Time left =', request.session.get_expiry_age())
    else:
        request.session['user'] = f'{USER_ID}'
        request.session.set_expiry(COOKIE_LIFE_SPAN)
        print('New user:', request.session['user'])
        print('Time left =', request.session.get_expiry_age())
    return request.session['user']
