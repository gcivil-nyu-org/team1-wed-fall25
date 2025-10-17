from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    # BROWSE & MANAGE (Phase 2)
    path("", views.index, name="index"),
    path("public/", views.public_events, name="public"),
    path("invitations/", views.invitations, name="invitations"),
    # CREATE (Phase 1)
    path("create/", views.create, name="create"),
    # ACTIONS (Phase 2)
    path("<slug:slug>/join/", views.join_event, name="join"),
    path("<slug:slug>/accept/", views.accept_invite, name="accept"),
    path("<slug:slug>/decline/", views.decline_invite, name="decline"),
    # DETAIL (stub for Phase 1, full in Phase 3)
    path("<slug:slug>/", views.detail, name="detail"),
    # HELPER APIs (autocomplete for create form & map pins)
    path(
        "api/locations/search/", views.api_locations_search, name="api_locations_search"
    ),
    path("api/users/search/", views.api_users_search, name="api_users_search"),
    path("api/pins/", views.api_event_pins, name="api_event_pins"),
]
