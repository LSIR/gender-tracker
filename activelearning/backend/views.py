from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .helpers import load_article, parse_xml
import json

def hello(request):
    return JsonResponse({'hello': 'world'})


def loadSentence(request):
    xml_article = load_article()
    response = parse_xml(xml_article)
    return JsonResponse(response)


@csrf_exempt 
def submitTags(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tags = data['tags']
            print(tags)
            return HttpResponse('Success.')
        except KeyError:
            tags = "error"
            print(tags)
            return HttpResponse('Failiure. JSON parse failed.')
    return HttpResponse('Failiure. Not a POST request.')

