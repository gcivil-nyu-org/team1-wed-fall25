from django.urls import path
from . import views

app_name = "loc_detail"

urlpatterns = [
    path("", views.index, name="index"),
    path("art/<int:art_id>/", views.art_detail, name="art_detail"),
]