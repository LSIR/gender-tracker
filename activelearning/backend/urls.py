from django.urls import path
from .views import hello, loadSentence, submitTags

urlpatterns = [
    path('hello/', hello),
    path('loadSentence/', loadSentence),
    path('submitTags/', submitTags),
]
