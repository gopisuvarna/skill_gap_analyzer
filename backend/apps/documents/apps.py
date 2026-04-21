'''It tells Django:
“This is an app. Here is its name, settings, and configuration.”'''

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'
    label = 'documents'


