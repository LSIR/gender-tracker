from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .helpers import load_article, parse_xml
import json

# The life span of a cookie, in seconds
COOKIE_LIFE_SPAN = 1 * 60 * 60


def loadSentence(request):
    """
    Returns a sentence that the user can label.
    """
    xml_article = load_article('../data/article01.xml')
    response = parse_xml(xml_article)
    return JsonResponse(response)


@csrf_exempt 
def submitTags(request):
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
    session = request.session
    session.set_test_cookie()
    print(session.keys())
    # Clears cookies that have expired
    session.clear_expired()
    # If the user already doesn't have a session yet,
    # set a cookie that expires COOKIE_LIFE_SPAN hour later
    print(session.keys())
    if 'user' not in session:
        session['user'] = '1'
        session.set_expiry(COOKIE_LIFE_SPAN)
        print('Cookie set. Life Span = 1 hour = 3600 seconds')
    else:
        print('Returning user:', session['user'])
        print('Time left =', session.get_expiry_age())

