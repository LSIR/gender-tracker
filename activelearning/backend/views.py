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

# The life span of a cookie, in seconds
COOKIE_LIFE_SPAN = 1 * 60 * 60

# If only a single label is needed for each sentence
ADMIN_TAGGER = True


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
    :return: Json A Json file containing the article_id, sentence_id, data and task.
    """
    user_id = session_load(request)
    labelling_task = request_labelling_task(user_id)
    if labelling_task is not None:
        return JsonResponse(labelling_task)
    else:
        return JsonResponse({'article_id': -1, 'sentence_id': [], 'data': [], 'task': 'None'})


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
            first_sentence = int(data['first_sentence'][0])
            return JsonResponse(load_paragraph_above(article_id, first_sentence))
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
            last_sentence = int(data['last_sentence'][0])
            return JsonResponse(load_paragraph_below(article_id, last_sentence))
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
            sent_id = data['sentence_id']
            first_sentence = data['first_sentence']
            last_sentence = data['last_sentence']
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
                sentence_confidences[first_sentence:last_sentence+1] = (last_sentence - first_sentence + 1) * [0]
                change_confidence(article_id, sentence_confidences)
            else:
                sentence_ends = article.sentences['sentences']
                clean_labels = clean_user_labels(sentence_ends, sent_id, first_sentence, last_sentence, labels, authors)
                for sentence in clean_labels:
                    add_user_label_to_db(user_id, article_id, sentence['index'], sentence['labels'],
                                         sentence['authors'], ADMIN_TAGGER)
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


















