from django.urls import path
from .views import submit_tags, load_content, load_rest_of_paragraph

urlpatterns = [
    path('loadContent/', load_content),
    path('loadMoreContent/', load_rest_of_paragraph),
    path('submitTags/', submit_tags),
]
