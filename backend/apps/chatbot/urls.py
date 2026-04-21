"""Chatbot URL routes."""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat),
]
