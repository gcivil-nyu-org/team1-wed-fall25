from django.urls import path
from . import views

app_name = "loc_detail"

urlpatterns = [
    path("", views.index, name="index"),
    path("art/<int:art_id>/", views.art_detail, name="art_detail"),
    path("favorites/", views.favorites, name="favorites"),
    # API endpoints
    path("api/points/all", views.api_all_points, name="api_all_points"),
    path(
        "api/favorite/<int:art_id>/toggle",  # noqa: E501
        views.api_favorite_toggle,
        name="api_favorite_toggle",
    ),
]
