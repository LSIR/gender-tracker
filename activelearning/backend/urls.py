from django.urls import path
from .views import hello, loadSentence

urlpatterns = [
    path('hello/', hello),
    path('loadSentence/', loadSentence)
]
