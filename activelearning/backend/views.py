from django.http import JsonResponse

def hello(request):
    return JsonResponse({'hello': 'world'})

def loadSentence(request):
    return JsonResponse({'sentence': 'George said that he will "never visit Lausanne, it rains too often".'})
