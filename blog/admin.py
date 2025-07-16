from django.contrib import admin

from blog.models import Article, UserReadRecord
admin.site.register(Article)
admin.site.register(UserReadRecord)
