from django.urls import path
from .views import submit_tags, load_content, load_above, load_below

urlpatterns = [
    path('loadContent/', load_content),
    path('loadAbove/', load_above),
    path('loadBelow/', load_below),
    path('submitTags/', submit_tags),
]
