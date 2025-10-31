"""
URL configuration for unified favorites
"""
from django.urls import path
from . import views

app_name = "favorites"

urlpatterns = [
    path("", views.favorites_view, name="index"),
]
