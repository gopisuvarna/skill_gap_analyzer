"""Recommendation URL routes."""
from django.urls import path
from . import views

urlpatterns = [
    path('roles/', views.top_roles),
    path('skill-gap/<uuid:role_id>/', views.skill_gap),
    path('learning-plan/<uuid:role_id>/', views.learning_plan),
]
