from django.urls import path
from . import views

app_name = "user_messages"

urlpatterns = [
    # Main pages
    path("", views.inbox, name="inbox"),
    path("users/", views.user_list, name="user_list"),
    path("conversation/<int:user_id>/", views.conversation_detail, name="conversation"),
    # API endpoints
    path("api/send/<int:user_id>/", views.send_message, name="send_message"),
    path("api/messages/<int:user_id>/", views.get_messages, name="get_messages"),
    path("api/unread-count/", views.unread_count, name="unread_count"),
    path("api/online-status/", views.update_online_status, name="update_online_status"),
    path(
        "api/delete/<int:conversation_id>/",
        views.delete_conversation,
        name="delete_conversation",
    ),
]
