from django.urls import path

from .views import submit_tags, load_content, load_above, load_below, become_admin, GetCounts

urlpatterns = [
    path('loadContent/', load_content),
    path('loadAbove/', load_above),
    path('loadBelow/', load_below),
    path('submitTags/', submit_tags),
    path('admin_tagger/', become_admin),
    path('get_counts', GetCounts.as_view()),
]
