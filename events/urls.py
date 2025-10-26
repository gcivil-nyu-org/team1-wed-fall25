from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    # BROWSE & MANAGE (Phase 2)
    path("", views.index, name="index"),
    path("public/", views.public_events, name="public"),
    path("invitations/", views.invitations, name="invitations"),
    path("favorites/", views.favorites, name="favorites"),
    # CREATE (Phase 1)
    path("create/", views.create, name="create"),
    # ACTIONS (Phase 2)
    path("<slug:slug>/join/", views.join_event, name="join"),
    path("<slug:slug>/accept/", views.accept_invite, name="accept"),
    path("<slug:slug>/decline/", views.decline_invite, name="decline"),
    # FAVORITES
    path("<slug:slug>/favorite/", views.favorite_event_view, name="favorite"),
    path("<slug:slug>/unfavorite/", views.unfavorite_event_view, name="unfavorite"),
    # UPDATE & DELETE (Host only)
    path("<slug:slug>/edit/", views.update_event, name="update"),
    path("<slug:slug>/delete/", views.delete_event, name="delete"),
    path("<slug:slug>/leave/", views.leave_event, name="leave"),
    # CHAT & REQUESTS (Phase 3)
    path("<slug:slug>/chat/send/", views.chat_send, name="chat_send"),
    path("<slug:slug>/request/", views.request_join_view, name="request_join"),
    path(
        "<slug:slug>/request/<int:request_id>/approve/",
        views.approve_request,
        name="approve_request",
    ),
    path(
        "<slug:slug>/request/<int:request_id>/decline/",
        views.decline_request,
        name="decline_request",
    ),
    # DETAIL (Phase 3 - fully implemented)
    path("<slug:slug>/", views.detail, name="detail"),
    # HELPER APIs (autocomplete for create form & map pins)
    path(
        "api/locations/search/", views.api_locations_search, name="api_locations_search"
    ),
    path("api/users/search/", views.api_users_search, name="api_users_search"),
    path("api/pins/", views.api_event_pins, name="api_event_pins"),
]
