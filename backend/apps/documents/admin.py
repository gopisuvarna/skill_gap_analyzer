from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    #Which columns appear in the admin list page.
    list_display = ('id', 'user', 'parsed', 'uploaded_at')
    #This adds a filter sidebar in admin.
    list_filter = ('parsed',)
