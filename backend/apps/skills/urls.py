"""Skill URL routes."""
from django.urls import path
from . import views

urlpatterns = [
    path('extract/', views.extract_from_document),
    path('', views.list_user_skills),
    path('manual/', views.add_user_skill),
    path('<uuid:pk>/', views.remove_user_skill),
]
