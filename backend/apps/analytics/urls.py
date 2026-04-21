"""Analytics URL routes."""
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard),
]
