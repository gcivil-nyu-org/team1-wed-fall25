from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = "loc_detail"

urlpatterns = [
    path("", views.index, name="index"),
    path("art/<int:art_id>/", views.art_detail, name="art_detail"),
    path(
        "favorites/",
        RedirectView.as_view(url="/favorites/?tab=art", permanent=False),
        name="favorites",
    ),
    # API endpoints
    path("api/points/all", views.api_all_points, name="api_all_points"),
    path(
        "api/favorite/<int:art_id>/toggle",
        views.api_favorite_toggle,
        name="api_favorite_toggle",
    ),
    path(
        "api/comment/<int:comment_id>/reaction",
        views.api_comment_reaction,
        name="api_comment_reaction",
    ),
]
