from django.urls import path
from .views import submit_tags, load_content

urlpatterns = [
    path('loadContent/', load_content),
    path('submitTags/', submit_tags),
]
