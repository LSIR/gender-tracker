from django.contrib import admin

from .models import Article, UserLabel

# Register your models here.
admin.site.register(Article)
admin.site.register(UserLabel)
