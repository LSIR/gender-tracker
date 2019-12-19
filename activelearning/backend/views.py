from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .task_loading import request_labelling_task, load_paragraph_above, load_paragraph_below
from .task_parsing import add_labels_to_database
import json
import uuid

# The life span of a cookie, in seconds
COOKIE_LIFE_SPAN = 1 * 60 * 60

# Default session ID (until the actual cookies are working)
USER_ID = 1111

# If in dev mode, don't touch the database:
ADMIN_TAGGER = False


def load_content(request):
    """
    Selects either a sentence or a paragraph that needs to be labelled. Creates a JSON file that contains an article_id
    (int), a paragraph_id (int), a sentence_id ([int]), data (list[string]) and a task (either 'sentence' if a
    sentence needs to be labelled or 'paragraph' if a paragraph needs to be labelled).

    If a sentence needs to be labelled, sentence_id is a list of a least one integer, and data is a list of individual
    tokens (words). If a paragraph needs to be annotated, sentence_id is an empty list, and data is a list containing a
    single string, which is the content of the entire paragraph.

    If no more labelling is required from a user, a simple JSon file will be returned containing only 'task': 'None'.

    :param request: The user request
    :return: Json A Json file containing the article_id, paragraph_id, sentence_id, data and task.
    """
    user_id = session_load(request)
    labelling_task = request_labelling_task(user_id)
    if labelling_task is not None:
        return JsonResponse(labelling_task)
    else:
        return JsonResponse({'task': 'None'})


def load_above(request):
    """
    Loads the tokens of the paragraph above a given sentence, or the whole paragraph if the sentence is in a paragraph
    below it.

    :param request:
        The user request.
    :return: Json.
        A Json file containing the the list of tokens of the paragraph above the sentence.
    """
    if request.method == 'GET':
        try:
            # Get user tags
            data = dict(request.GET)
            article_id = int(data['article_id'][0])
            paragraph_id = int(data['paragraph_id'][0])
            sentence_id = int(data['sentence_id'][0])
            return JsonResponse(load_paragraph_above(article_id, paragraph_id, sentence_id))
        except KeyError:
            return JsonResponse({'Success': False, 'reason': 'KeyError'})
    return JsonResponse({'Success': False, 'reason': 'not GET'})


def load_below(request):
    """
    Loads the tokens of the paragraph below a given sentence, or the whole paragraph if the sentence is in a paragraph
    above it.

    :param request:
        The user request.
    :return: Json.
        A Json file containing the the list of tokens of the paragraph above the sentence.
    """
    if request.method == 'GET':
        try:
            # Get user tags
            data = dict(request.GET)
            article_id = int(data['article_id'][0])
            paragraph_id = int(data['paragraph_id'][0])
            sentence_id = int(data['sentence_id'][0])
            return JsonResponse(load_paragraph_below(article_id, paragraph_id, sentence_id))
        except KeyError:
            return JsonResponse({'Success': False, 'reason': 'KeyError'})
    return JsonResponse({'Success': False, 'reason': 'not GET'})


@csrf_exempt
def submit_tags(request):
    """

    :param request:
    :return:
    """
    # Session stuff
    user_id = session_post(request)
    if user_id is None:
        return JsonResponse({'success': False, 'reason': 'cookies'})
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            article_id = data['article_id']
            paragraph_id = data['paragraph_id']
            sent_id = data['sentence_id']
            tags = data['tags']
            authors = data['authors']

            add_labels_to_database(user_id, article_id, paragraph_id, sent_id, tags, authors, ADMIN_TAGGER)
            return JsonResponse({'success': True})
        except KeyError:
            return JsonResponse({'success': False, 'reason': 'KeyError'})
    return JsonResponse({'success': False, 'reason': 'not POST'})


def session_load(request):
    """

    :param request:
    :return:
    """
    if 'id' in request.session:
        return request.session['id']
    else:
        request.session.set_test_cookie()
        user_id = str(uuid.uuid1())
        request.session['id'] = user_id
        return user_id


def session_post(request):
    """

    :param request:
    :return:
    """
    if 'id' not in request.session:
        return None

    return request.session['id']


















