from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.urls import reverse

from .models import Event, EventInvite
from .forms import EventForm, parse_locations, parse_invites
from .services import (
    create_event,
    join_event as join_event_service,
    accept_invite as accept_invite_service,
    decline_invite as decline_invite_service,
)
from .selectors import (
    search_locations,
    search_users,
    public_event_pins,
    list_public_events,
    user_has_joined,
    list_user_invitations,
)
from .enums import InviteStatus, MessageReportReason
from .models import EventChatMessage, MessageReport


@login_required
def create(request):
    """Create a new event"""
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            try:
                locations = parse_locations(request)
                invites = parse_invites(request)

                event = create_event(
                    host=request.user, form=form, locations=locations, invites=invites
                )

                messages.success(
                    request, f'Event "{event.title}" created successfully!'
                )
                return redirect(event.get_absolute_url())

            except ValueError as e:
                messages.error(request, str(e))
            except ValidationError as e:
                # Show the actual validation error message
                error_msg = e.message if hasattr(e, "message") else str(e)
                messages.error(request, error_msg)
            except Exception as e:
                # Show the specific error during development
                messages.error(request, f"An error occurred: {str(e)}")
    else:
        form = EventForm()

    return render(request, "events/create.html", {"form": form})


@login_required
def detail(request, slug):
    """
    Event detail page with dynamic content based on user role

    Context varies by role:
    - HOST/ATTENDEE: Full details + chat + members + join requests (host only)
    - VISITOR: Read-only details + join/request button
    """
    from .selectors import (
        get_event_detail,
        user_role_in_event,
        list_event_attendees,
        list_chat_messages,
        get_join_request,
        list_pending_join_requests,
    )
    from .models import EventFavorite

    try:
        event = get_event_detail(slug)
    except Event.DoesNotExist:
        messages.error(request, "Event not found.")
        return redirect("events:public")

    user_role = user_role_in_event(event, request.user)

    # Get additional locations (ordered stops)
    additional_locations = event.locations.all().order_by("order")

    # Get attendees list
    attendees = list_event_attendees(event)

    # Check if user has favorited this event
    is_favorited = EventFavorite.objects.filter(event=event, user=request.user).exists()

    context = {
        "event": event,
        "user_role": user_role,
        "additional_locations": additional_locations,
        "attendees": attendees,
        "is_favorited": is_favorited,
    }

    # Participant-specific data
    if user_role in ["HOST", "ATTENDEE"]:
        context["chat_messages"] = list_chat_messages(event, limit=20)

        # Host-specific data
        if user_role == "HOST":
            context["join_requests"] = list_pending_join_requests(event)

    # Visitor-specific data
    if user_role == "VISITOR":
        context["join_request"] = get_join_request(event, request.user)

    return render(request, "events/detail.html", context)


@login_required
def index(request):
    """Redirect to public events as default"""
    return redirect("events:public")


@login_required
def public_events(request):
    """Display public events with search, filter, and pagination"""
    from .models import EventFavorite

    # Parse query params
    query = request.GET.get("q", "").strip()
    visibility_filter = request.GET.get("filter", "")  # 'open' or 'invite'
    sort = request.GET.get("sort", "start_time")  # 'start_time' or '-start_time'

    # Get events
    events = list_public_events(
        query=query if query else None,
        visibility_filter=visibility_filter if visibility_filter else None,
        order=sort,
    )

    # Get user's favorited event IDs for efficient lookup
    favorited_ids = set(
        EventFavorite.objects.filter(user=request.user).values_list(
            "event_id", flat=True
        )
    )

    # Add 'joined' and 'is_favorited' attributes to each event
    events_list = []
    for event in events:
        event.joined = user_has_joined(event, request.user)
        event.is_favorited = event.id in favorited_ids
        events_list.append(event)

    # Pagination
    paginator = Paginator(events_list, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "query": query,
        "filter": visibility_filter,
        "sort": sort,
    }

    return render(request, "events/public_events.html", context)


@login_required
@require_POST
def join_event(request, slug):
    """Join a public event"""
    event = get_object_or_404(Event, slug=slug)

    try:
        join_event_service(event=event, user=request.user)
        messages.success(request, f'You have joined "{event.title}"!')
    except ValueError as e:
        messages.error(request, str(e))

    # Redirect back to public events with query params preserved
    redirect_url = reverse("events:public")
    query_params = request.GET.urlencode()
    if query_params:
        redirect_url += f"?{query_params}"

    return redirect(redirect_url)


@login_required
def invitations(request):
    """Display pending invitations for current user"""
    invites = list_user_invitations(request.user)

    return render(request, "events/invitations.html", {"invites": invites})


@login_required
@require_POST
def accept_invite(request, slug):
    """Accept an invitation"""
    event = get_object_or_404(Event, slug=slug)
    invite = get_object_or_404(
        EventInvite, event=event, invitee=request.user, status=InviteStatus.PENDING
    )

    try:
        accept_invite_service(invite=invite)
        messages.success(
            request, f'You have accepted the invitation to "{event.title}"!'
        )
        return redirect(event.get_absolute_url())
    except Exception:
        messages.error(request, "Failed to accept invitation.")
        return redirect("events:invitations")


@login_required
@require_POST
def decline_invite(request, slug):
    """Decline an invitation"""
    event = get_object_or_404(Event, slug=slug)
    invite = get_object_or_404(
        EventInvite, event=event, invitee=request.user, status=InviteStatus.PENDING
    )

    try:
        decline_invite_service(invite=invite)
        messages.success(request, "Invitation declined.")
    except Exception:
        messages.error(request, "Failed to decline invitation.")

    return redirect("events:invitations")


@login_required
def api_locations_search(request):
    """JSON API for location autocomplete"""
    term = request.GET.get("q", "").strip()

    if not term or len(term) < 2:
        return JsonResponse({"results": []})

    locations = search_locations(term, limit=10)

    # Return compact format matching map style
    results = [
        {
            "id": loc["id"],
            "t": loc["title"] or "Untitled",
            "a": loc["artist_name"] or "Unknown",
            "y": float(loc["latitude"]),
            "x": float(loc["longitude"]),
        }
        for loc in locations
    ]

    return JsonResponse({"results": results})


@login_required
def api_users_search(request):
    """JSON API for user autocomplete"""
    term = request.GET.get("q", "").strip()

    if not term or len(term) < 2:
        return JsonResponse({"results": []})

    users = search_users(term, limit=10)

    results = [{"id": user["id"], "u": user["username"]} for user in users]

    return JsonResponse({"results": results})


@login_required
def api_event_pins(request):
    """JSON API for event pins on map"""
    events = public_event_pins()

    points = [
        {
            "id": event["id"],
            "t": event["title"],
            "y": float(event["start_location__latitude"]),
            "x": float(event["start_location__longitude"]),
            "slug": event["slug"],
        }
        for event in events
    ]

    return JsonResponse({"points": points})


@login_required
def api_chat_messages(request, slug):
    """JSON API for real-time chat messages"""
    from .selectors import list_chat_messages, user_role_in_event

    event = get_object_or_404(Event, slug=slug)

    # Check if user is a member
    role = user_role_in_event(event, request.user)
    if role == "VISITOR":
        return JsonResponse({"error": "Only event members can view chat"}, status=403)

    # Get messages
    messages = list_chat_messages(event, limit=20)

    # Format for JSON response
    messages_data = [
        {
            "id": msg.id,
            "author": msg.author.username,
            "is_host": msg.author == event.host,
            "message": msg.message,
            "created_at": msg.created_at.strftime("%b %d, %I:%M %p"),
        }
        for msg in messages
    ]

    return JsonResponse({"messages": messages_data})


# PHASE 3 VIEWS


@login_required
@require_POST
def chat_send(request, slug):
    """Send a chat message"""
    from .services import post_chat_message as post_chat_service

    event = get_object_or_404(Event, slug=slug)
    message = request.POST.get("message", "").strip()

    try:
        post_chat_service(event=event, user=request.user, message=message)
        messages.success(request, "Message sent!")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect(event.get_absolute_url() + "#chat")


@login_required
@require_POST
def request_join_view(request, slug):
    """Request to join a PUBLIC_INVITE event"""
    from .services import request_join as request_join_service

    event = get_object_or_404(Event, slug=slug)

    try:
        request_join_service(event=event, user=request.user)
        messages.success(request, "Join request sent to host!")
    except ValueError as e:
        messages.error(request, str(e))

    return redirect(event.get_absolute_url())


@login_required
@require_POST
def approve_request(request, slug, request_id):
    """Host approves a join request"""
    from .services import approve_join_request as approve_service
    from .models import EventJoinRequest

    event = get_object_or_404(Event, slug=slug)

    # Verify user is host
    if event.host != request.user:
        messages.error(request, "Only the host can manage join requests.")
        return redirect(event.get_absolute_url())

    join_request = get_object_or_404(EventJoinRequest, id=request_id, event=event)

    try:
        approve_service(join_request=join_request)
        messages.success(
            request, f"{join_request.requester.username} has been added to the event!"
        )
    except Exception:
        messages.error(request, "Failed to approve request.")

    return redirect(event.get_absolute_url())


@login_required
@require_POST
def decline_request(request, slug, request_id):
    """Host declines a join request"""
    from .services import decline_join_request as decline_service
    from .models import EventJoinRequest

    event = get_object_or_404(Event, slug=slug)

    # Verify user is host
    if event.host != request.user:
        messages.error(request, "Only the host can manage join requests.")
        return redirect(event.get_absolute_url())

    join_request = get_object_or_404(EventJoinRequest, id=request_id, event=event)

    try:
        decline_service(join_request=join_request)
        messages.success(request, "Join request declined.")
    except Exception:
        messages.error(request, "Failed to decline request.")

    return redirect(event.get_absolute_url())


@login_required
def update_event(request, slug):
    """Update an existing event (host only)"""
    from .services import update_event as update_event_service

    event = get_object_or_404(Event, slug=slug, is_deleted=False)

    # Verify user is host
    if event.host != request.user:
        messages.error(request, "Only the host can edit this event.")
        return redirect(event.get_absolute_url())

    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            try:
                locations = parse_locations(request)
                invites = parse_invites(request)

                updated_event = update_event_service(
                    event=event, form=form, locations=locations, invites=invites
                )

                messages.success(request, f'Event "{updated_event.title}" updated!')
                return redirect(updated_event.get_absolute_url())

            except ValueError as e:
                messages.error(request, str(e))
            except ValidationError as e:
                error_msg = e.message if hasattr(e, "message") else str(e)
                messages.error(request, error_msg)
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
    else:
        # Pre-populate form with existing data
        form = EventForm(instance=event)

    # Get existing locations and invites for pre-population
    existing_locations = list(
        event.locations.all().order_by("order").values_list("location_id", flat=True)
    )
    existing_invites = list(
        EventInvite.objects.filter(event=event).values_list("invitee_id", flat=True)
    )

    context = {
        "form": form,
        "event": event,
        "existing_locations": existing_locations,
        "existing_invites": existing_invites,
        "is_update": True,
    }

    return render(request, "events/create.html", context)


@login_required
@require_POST
def delete_event(request, slug):
    """Delete an event (host only)"""
    from .services import delete_event as delete_event_service

    event = get_object_or_404(Event, slug=slug, is_deleted=False)

    # Verify user is host
    if event.host != request.user:
        messages.error(request, "Only the host can delete this event.")
        return redirect(event.get_absolute_url())

    try:
        delete_event_service(event=event)
        messages.success(request, f'Event "{event.title}" has been deleted.')
        return redirect("events:public")
    except Exception as e:
        messages.error(request, f"Failed to delete event: {str(e)}")
        return redirect(event.get_absolute_url())


@login_required
@require_POST
def leave_event(request, slug):
    """Leave an event (attendee deregistration)"""
    from .services import leave_event as leave_event_service

    event = get_object_or_404(Event, slug=slug, is_deleted=False)

    try:
        leave_event_service(event=event, user=request.user)
        messages.success(request, f'You have left "{event.title}".')
        return redirect("events:public")
    except ValueError as e:
        messages.error(request, str(e))
        return redirect(event.get_absolute_url())


@login_required
@require_POST
def favorite_event_view(request, slug):
    """Add event to favorites"""
    from .services import favorite_event as favorite_event_service

    event = get_object_or_404(Event, slug=slug, is_deleted=False)

    try:
        favorite_event_service(event=event, user=request.user)
        messages.success(request, f'Added "{event.title}" to favorites!')
    except ValueError as e:
        messages.error(request, str(e))

    # Redirect back to the referring page or event detail
    return redirect(request.META.get("HTTP_REFERER", event.get_absolute_url()))


@login_required
@require_POST
def unfavorite_event_view(request, slug):
    """Remove event from favorites"""
    from .services import unfavorite_event as unfavorite_event_service

    event = get_object_or_404(Event, slug=slug)

    try:
        unfavorite_event_service(event=event, user=request.user)
        messages.success(request, f'Removed "{event.title}" from favorites.')
    except Exception as e:
        messages.error(request, f"Failed to remove from favorites: {str(e)}")

    # Redirect back to the referring page or event detail
    return redirect(request.META.get("HTTP_REFERER", event.get_absolute_url()))


@login_required
def favorites(request):
    """Display user's favorite events"""
    from .models import EventFavorite

    # Get favorited events (excluding deleted ones)
    favorites_qs = (
        EventFavorite.objects.filter(user=request.user, event__is_deleted=False)
        .select_related("event", "event__host", "event__start_location")
        .order_by("-created_at")
    )

    # Add 'joined' attribute to each event
    favorites_list = []
    for fav in favorites_qs:
        fav.event.joined = user_has_joined(fav.event, request.user)
        fav.event.favorited_at = fav.created_at
        favorites_list.append(fav.event)

    # Pagination
    paginator = Paginator(favorites_list, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
    }

    return render(request, "events/favorites.html", context)


@login_required
@require_POST
def report_message(request, message_id):
    """Report an inappropriate chat message"""
    from .enums import ReportStatus
    from django.utils import timezone
    
    message = get_object_or_404(EventChatMessage, id=message_id)
    
    # Get reason and description from POST data
    reason = request.POST.get("reason")
    description = request.POST.get("description", "").strip()
    
    # Validate reason
    if not reason or reason not in [choice[0] for choice in MessageReportReason.choices]:
        return JsonResponse({"error": "Invalid reason"}, status=400)
    
    # Check if user already reported this message
    existing_report = MessageReport.objects.filter(
        message=message, reporter=request.user
    ).exists()
    
    if existing_report:
        return JsonResponse({"error": "You have already reported this message"}, status=400)
    
    # Create report
    report = MessageReport.objects.create(
        message=message,
        reporter=request.user,
        reason=reason,
        description=description,
        status=ReportStatus.PENDING
    )
    
    return JsonResponse({
        "success": True,
        "message": "Message reported successfully"
    })
