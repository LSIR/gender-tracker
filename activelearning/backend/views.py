from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist

from backend.frontend_parsing.postgre_to_frontend import load_paragraph_above, load_paragraph_below
from backend.frontend_parsing.frontend_to_postgre import clean_user_labels
from backend.db_management import add_user_label_to_db, request_labelling_task
from backend.helpers import change_confidence
from .models import Article
import json
import uuid

import sys, traceback

# The life span of a cookie, in seconds
COOKIE_LIFE_SPAN = 1 * 60 * 60

# The key needed to become an admin
ADMIN_SECRET_KEY = 'i_want_to_be_admin'


def load_content(request):
    """
    Selects either a sentence or a paragraph that needs to be labelled. Creates a JSON file that contains an article_id
    (an integer), sentence_ids (a list of integers), data (a list of strings), a task (a string: 'sentence' if a
    sentence needs to be labelled, 'paragraph' if a whole paragraph needs to be labelled, 'None' if there are no more
    sentences to label in the database and 'error' if an error happened in the backend) and a boolean 'admin value',
    which is true is the user has been assigned as an admin.

    If a sentence needs to be labelled, sentence_id is a list of a least one integer, and data is a list of individual
    tokens (words). If a paragraph needs to be annotated, sentence_id is an empty list, and data is a list containing a
    single string, which is the content of the entire paragraph.

    If the task is 'None', then the article ID is -1 and both the sentence id and data are empty lists.

    :param request: HTTP GET Request
        The request with the
    :return: JsonResponse
        A Json file containing the 'article_id', 'sentence_id', 'data', 'task' and 'admin'.
    """
    user_id, admin_tagger = session_load(request)
    labelling_task = request_labelling_task(user_id)
    if labelling_task is not None:
        labelling_task['admin'] = admin_tagger
        return JsonResponse(labelling_task)
    else:
        return JsonResponse({'article_id': -1, 'sentence_id': [], 'data': [], 'task': 'None', 'admin': admin_tagger})


def load_above(request):
    """
    Loads the tokens of the paragraph above a given sentence, or the whole paragraph if the sentence is in a paragraph
    below it. Forms a Json file that always contains the key 'Success'.

    If the value of 'Success' is true, then the Json also contains 'data' (a list of strings), 'first_sentence' (an
    integer representing the index of the first sentence who's tokens are in data) and 'last_sentence' (an integer
    representing the index of the last sentence who's tokens are in data).

    If the value of 'Success' is false, then the Json also contains the 'reason' key, which has as a value either
    'KeyError' (if one of the required parameters of the GET request wasn't there) or 'not GET' (if the request wasn't a
    GET request).

    :param request: HTTP GET Request
        The user request, with a Json payload containing two keys: 'article_id' and 'first_sentence'
    :return: JsonResponse
        A Json file containing the the list of tokens of the paragraph above the sentence.
    """
    if request.method == 'GET':
        try:
            # Get user tags
            data = dict(request.GET)
            article_id = int(data['article_id'][0])
            first_sentence = int(data['first_sentence'][0])
            data = load_paragraph_above(article_id, first_sentence)
            data['Success'] = True
            return JsonResponse(data)
        except KeyError:
            return JsonResponse({'Success': False, 'reason': 'KeyError'})
    return JsonResponse({'Success': False, 'reason': 'not GET'})


def load_below(request):
    """
    Loads the tokens of the paragraph below a given sentence, or the whole paragraph if the sentence is in a paragraph
    above it. Forms a Json file that always contains the key 'Success'.

    If the value of 'Success' is true, then the Json also contains 'data' (a list of strings), 'first_sentence' (an
    integer representing the index of the first sentence who's tokens are in data) and 'last_sentence' (an integer
    representing the index of the last sentence who's tokens are in data).

    If the value of 'Success' is false, then the Json also contains the 'reason' key, which has as a value either
    'KeyError' (if one of the required parameters of the GET request wasn't there) or 'not GET' (if the request wasn't a
    GET request).

    :param request: HTTP GET Request
        The user request, with a Json payload containing two keys: 'article_id' and 'last_sentence'
    :return: JsonResponse
        A Json file containing the list of tokens of the paragraph below the sentence.
    """
    if request.method == 'GET':
        try:
            # Get user tags
            data = dict(request.GET)
            article_id = int(data['article_id'][0])
            last_sentence = int(data['last_sentence'][0])
            data = load_paragraph_below(article_id, last_sentence)
            data['Success'] = True
            return JsonResponse(data)
        except KeyError:
            return JsonResponse({'Success': False, 'reason': 'KeyError'})
    return JsonResponse({'Success': False, 'reason': 'not GET'})


@csrf_exempt
def submit_tags(request):
    """
    Adds the labels a user created to the database.

    :param request: HTTP POST request
        A post request containing the labels the user created. Contains the following keys.
            * 'article_id': The id of the article that the user annotated.
            * 'sentence_id': The list of sentence indices that the user annotated.
            * 'first_sentence': The index of the first sentence who's tokens are in tags
            * 'last_sentence': The index of the last sentence who's tokens are in tags
            * 'tags': A list of tags for each token in the sentences.
            * 'authors': A list of token indices that are authors of the quote, and an empty list if no reported speech
                            was in the sentences.
            * 'task': The task that the user performed ('sentence' or 'paragraph').
    :return: JsonResponse
        A Json containing the key 'success'. If it's value is false, also contains a key 'reason' that can have values
        'not POST' (if the request wasn't a POST request) or 'KeyError' (if a key was missing from the request).
    """
    # Session stuff
    user_id, admin_tagger = session_post(request)
    if user_id is None:
        return JsonResponse({'success': False, 'reason': 'cookies'})
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            article_id = data['article_id']
            sent_id = data['sentence_id']
            first_sent = data['first_sentence']
            last_sent = data['last_sentence']
            labels = data['tags']
            authors = data['authors']
            task = data['task']

            try:
                article = Article.objects.get(id=article_id)
            except ObjectDoesNotExist:
                return JsonResponse({'success': False, 'reason': 'Invalid Article ID'})

            # If the task was to label a paragraph, and the user answered that there were some quotes in the paragraph,
            # reset the confidences for the whole paragraph to 0.
            if task == 'paragraph' and sum(labels) > 0:
                sentence_confidences = article.confidence['confidence'].copy()
                sentence_confidences[first_sent:last_sent + 1] = (last_sent - first_sent + 1) * [0]
                change_confidence(article_id, sentence_confidences)
            else:
                sentence_ends = article.sentences['sentences']
                clean_labels = clean_user_labels(sentence_ends, sent_id, first_sent, last_sent, labels, authors)
                for sentence in clean_labels:
                    add_user_label_to_db(user_id, article_id, sentence['index'], sentence['labels'],
                                         sentence['authors'], admin_tagger)
            return JsonResponse({'success': True})
        except KeyError:
            traceback.print_exc(file=sys.stdout)
            return JsonResponse({'success': False, 'reason': 'KeyError'})
    return JsonResponse({'success': False, 'reason': 'not POST'})


def session_load(request):
    """
    Checks if the user already has a session key. If they don't, create one.

    :param request: HTTP Request
        The request from the user.
    :return: string, boolean
        The user's id.
        If the user is admin.
    """
    if 'id' in request.session:
        user_id = request.session['id']
    else:
        request.session.set_test_cookie()
        user_id = str(uuid.uuid1())
        request.session['id'] = user_id
    admin_tagger = False
    if 'admin' in request.session and request.session['admin']:
        admin_tagger = True
    return user_id, admin_tagger


def session_post(request):
    """
    Checks if the user has a session key.

    :param request: HTTP Request
        The request from the user.
    :return: string, boolean
        The user's id, or None if the user hasn't been assigned an ID.
        If the user is admin.
    """
    if 'id' not in request.session:
        return None
    admin_tagger = False
    if 'admin' in request.session and request.session['admin']:
        admin_tagger = True
    return request.session['id'], admin_tagger


def become_admin(request):
    """
    Assigns an admin cookie to the user, if and only if they have the correct key as a parameter.

    :param request: HTTP GET Request
        The user request. Must contain a 'key' parameter with the correct value for the user to become an admin.
    :return: JsonResponse
        A Json containing the key 'Success', with value True if the user became an admin and false otherwise.
    """
    # Get user secret key
    data = dict(request.GET)
    secret_key = data['key'][0]
    if secret_key == ADMIN_SECRET_KEY:
        request.session['admin'] = True
        return JsonResponse({'Success': True})

    return JsonResponse({'Success': False})
