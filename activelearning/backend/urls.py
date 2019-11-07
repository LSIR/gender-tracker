from django.urls import path
from .views import loadSentence, submitTags, load_content

urlpatterns = [
    path('loadSentence/', loadSentence),
    path('loadContent/', load_content),
    path('submitTags/', submitTags),
]
