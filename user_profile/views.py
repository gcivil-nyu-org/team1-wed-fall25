from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST

from .models import UserProfile, UserFollow
from .forms import UserProfileForm, UserBasicInfoForm
from events.models import Event, EventMembership
from events.enums import EventVisibility, MembershipRole
from loc_detail.models import UserFavoriteArt


@login_required
def profile_view(request, username=None):
    """View user profile - own or another user's"""
    if username:
        profile_user = get_object_or_404(User, username=username)
        is_own_profile = request.user == profile_user
    else:
        profile_user = request.user
        is_own_profile = True

    profile, created = UserProfile.objects.get_or_create(user=profile_user)

    can_view = is_own_profile or profile.is_public()

    if not can_view:
        messages.error(request, "This profile is private.")
        return redirect("artinerary:index")

    is_following = False
    if request.user.is_authenticated and not is_own_profile:
        is_following = UserFollow.objects.filter(
            follower=request.user, following=profile_user
        ).exists()

    if is_own_profile:
        hosted_events = Event.objects.filter(
            host=profile_user, is_deleted=False
        ).select_related("start_location")[:6]
    else:
        hosted_events = Event.objects.filter(
            host=profile_user,
            is_deleted=False,
            visibility__in=[
                EventVisibility.PUBLIC_OPEN,
                EventVisibility.PUBLIC_INVITE,
            ],
        ).select_related("start_location")[:6]

    favorite_art_count = UserFavoriteArt.objects.filter(user=profile_user).count()
    followers_count = profile_user.followers.count()
    following_count = profile_user.following.count()

    attended_events_count = EventMembership.objects.filter(
        user=profile_user, role=MembershipRole.ATTENDEE
    ).count()

    context = {
        "profile_user": profile_user,
        "profile": profile,
        "is_own_profile": is_own_profile,
        "is_following": is_following,
        "hosted_events": hosted_events,
        "favorite_art_count": favorite_art_count,
        "followers_count": followers_count,
        "following_count": following_count,
        "attended_events_count": attended_events_count,
    }

    return render(request, "user_profile/profile.html", context)


@login_required
def edit_profile(request):
    """Edit user profile"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        user_form = UserBasicInfoForm(request.POST, instance=request.user)

        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect("user_profile:profile_view", username=request.user.username)
    else:
        profile_form = UserProfileForm(instance=profile)
        user_form = UserBasicInfoForm(instance=request.user)

    context = {"profile_form": profile_form, "user_form": user_form}

    return render(request, "user_profile/edit_profile.html", context)


@login_required
@require_POST
def remove_profile_image(request):
    """Remove user's profile image"""
    try:
        profile = UserProfile.objects.get(user=request.user)

        if profile.profile_image:
            try:
                profile.profile_image.delete(save=False)
            except Exception as e:
                print(f"Error deleting file from storage: {e}")

            profile.profile_image = None
            profile.save()

            messages.success(request, "Profile image removed successfully!")
        else:
            messages.info(request, "No profile image to remove.")

    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
    except Exception as e:
        print(f"Error in remove_profile_image: {e}")
        messages.error(request, "An error occurred while removing the image.")

    return redirect("user_profile:edit_profile")


@login_required
def follow_user(request, username):
    """Follow a user"""
    if request.method != "POST":
        return redirect("user_profile:profile_view", username=username)

    user_to_follow = get_object_or_404(User, username=username)

    if user_to_follow == request.user:
        messages.error(request, "You cannot follow yourself.")
        return redirect("user_profile:profile_view", username=username)

    follow, created = UserFollow.objects.get_or_create(
        follower=request.user, following=user_to_follow
    )

    if created:
        messages.success(request, f"You are now following {username}!")
    else:
        messages.info(request, f"You are already following {username}.")

    return redirect("user_profile:profile_view", username=username)


@login_required
def unfollow_user(request, username):
    """Unfollow a user"""
    if request.method != "POST":
        return redirect("user_profile:profile_view", username=username)

    user_to_unfollow = get_object_or_404(User, username=username)

    deleted_count, _ = UserFollow.objects.filter(
        follower=request.user, following=user_to_unfollow
    ).delete()

    if deleted_count > 0:
        messages.success(request, f"You have unfollowed {username}.")
    else:
        messages.info(request, f"You were not following {username}.")

    return redirect("user_profile:profile_view", username=username)


@login_required
def followers_list(request, username):
    """List user's followers"""
    profile_user = get_object_or_404(User, username=username)
    is_own_profile = request.user == profile_user

    profile = get_object_or_404(UserProfile, user=profile_user)
    if not is_own_profile and not profile.is_public():
        messages.error(request, "This profile is private.")
        return redirect("artinerary:index")

    followers = (
        UserFollow.objects.filter(following=profile_user)
        .select_related("follower", "follower__profile")
        .order_by("-created_at")
    )

    paginator = Paginator(followers, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "profile_user": profile_user,
        "page_obj": page_obj,
        "is_own_profile": is_own_profile,
        "list_type": "followers",
    }

    return render(request, "user_profile/follow_list.html", context)


@login_required
def following_list(request, username):
    """List users that this user follows"""
    profile_user = get_object_or_404(User, username=username)
    is_own_profile = request.user == profile_user

    profile = get_object_or_404(UserProfile, user=profile_user)
    if not is_own_profile and not profile.is_public():
        messages.error(request, "This profile is private.")
        return redirect("artinerary:index")

    following = (
        UserFollow.objects.filter(follower=profile_user)
        .select_related("following", "following__profile")
        .order_by("-created_at")
    )

    paginator = Paginator(following, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "profile_user": profile_user,
        "page_obj": page_obj,
        "is_own_profile": is_own_profile,
        "list_type": "following",
    }

    return render(request, "user_profile/follow_list.html", context)


@login_required
def user_search(request):
    """Search for users"""
    query = request.GET.get("q", "").strip()

    if query:
        users = (
            User.objects.filter(
                Q(username__icontains=query) | Q(profile__full_name__icontains=query),
                profile__privacy="PUBLIC",
            )
            .select_related("profile")
            .distinct()[:20]
        )
    else:
        users = []

    context = {"query": query, "users": users}

    return render(request, "user_profile/user_search.html", context)
