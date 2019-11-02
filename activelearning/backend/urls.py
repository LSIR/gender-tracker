from django.urls import path
from .views import loadSentence, submitTags

urlpatterns = [
    path('loadSentence/', loadSentence),
    path('submitTags/', submitTags),
]
