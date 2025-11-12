from django.urls import path
from . import views

app_name = "user_profile"

urlpatterns = [
    # Profile views
    path(
        "remove-profile-image/", views.remove_profile_image, name="remove_profile_image"
    ),
    path("edit/profile/", views.edit_profile, name="edit_profile"),
    path("verify-email-change/", views.verify_email_change, name="verify_email_change"),
    path(
        "resend-email-change-otp/",
        views.resend_email_change_otp,
        name="resend_email_change_otp",
    ),
    path("", views.profile_view, name="my_profile"),
    path("<str:username>/", views.profile_view, name="profile_view"),
    # Follow functionality
    path("<str:username>/follow/", views.follow_user, name="follow_user"),
    path("<str:username>/unfollow/", views.unfollow_user, name="unfollow_user"),
    path("<str:username>/followers/", views.followers_list, name="followers_list"),
    path("<str:username>/following/", views.following_list, name="following_list"),
    # User search
    path("search/users/", views.user_search, name="user_search"),
]
