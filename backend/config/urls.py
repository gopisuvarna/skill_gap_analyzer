"""Main URL configuration."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/documents/', include('apps.documents.urls')),
    path('api/skills/', include('apps.skills.urls')),
    path('api/roles/', include('apps.roles.urls')),
    path('api/recommendations/', include('apps.recommendations.urls')),
    path('api/jobs/', include('apps.jobs.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/chatbot/', include('apps.chatbot.urls')),
]
