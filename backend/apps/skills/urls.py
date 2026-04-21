"""Skill URL routes."""
from django.urls import path
from . import views

urlpatterns = [
    path('extract/', views.extract_from_document),
    path('', views.user_skills),
    path('<uuid:pk>/', views.remove_user_skill),
]
