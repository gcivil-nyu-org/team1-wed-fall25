from django.db.models import Q
from django.contrib.auth import get_user_model
from loc_detail.models import PublicArt

User = get_user_model()


def search_locations(term, limit=10):
    """Search for art locations by title, artist, or location name"""
    return PublicArt.objects.filter(
        Q(title__icontains=term)
        | Q(artist_name__icontains=term)
        | Q(location__icontains=term),
        latitude__isnull=False,
        longitude__isnull=False,
    ).values("id", "title", "artist_name", "latitude", "longitude")[:limit]


def search_users(term, limit=10):
    """Search for users by username or email"""
    return User.objects.filter(
        Q(username__icontains=term) | Q(email__icontains=term)
    ).values("id", "username")[:limit]


def public_event_pins():
    """Get public event pins for map display"""
    from .models import Event
    from .enums import EventVisibility

    return (
        Event.objects.filter(
            visibility__in=[EventVisibility.PUBLIC_OPEN, EventVisibility.PUBLIC_INVITE],
            is_deleted=False,
        )
        .select_related("start_location")
        .values(
            "id",
            "slug",
            "title",
            "start_location__latitude",
            "start_location__longitude",
        )
    )


def list_public_events(query=None, visibility_filter=None, order="start_time"):
    """
    List public events with optional filtering and ordering

    Args:
        query: Search term for title, host username, location
        visibility_filter: 'open' or 'invite' to filter by visibility
        order: 'start_time' or '-start_time' for ascending/descending

    Returns:
        QuerySet of Event objects
    """
    from .models import Event
    from .enums import EventVisibility

    # Base queryset: public events only, not deleted
    qs = Event.objects.filter(
        visibility__in=[EventVisibility.PUBLIC_OPEN, EventVisibility.PUBLIC_INVITE],
        is_deleted=False,
    ).select_related("host", "start_location")

    # Search filter
    if query:
        qs = qs.filter(
            Q(title__icontains=query)
            | Q(host__username__icontains=query)
            | Q(start_location__title__icontains=query)
        )

    # Visibility filter
    if visibility_filter == "open":
        qs = qs.filter(visibility=EventVisibility.PUBLIC_OPEN)
    elif visibility_filter == "invite":
        qs = qs.filter(visibility=EventVisibility.PUBLIC_INVITE)

    # Ordering
    return qs.order_by(order)


def user_has_joined(event, user):
    """Check if user has joined event (HOST or ATTENDEE)"""
    from .models import EventMembership
    from .enums import MembershipRole

    return EventMembership.objects.filter(
        event=event, user=user, role__in=[MembershipRole.HOST, MembershipRole.ATTENDEE]
    ).exists()


def list_user_invitations(user):
    """
    Get pending invitations for a user

    Returns:
        QuerySet of EventInvite objects with event, host, location prefetched
    """
    from .models import EventInvite
    from .enums import InviteStatus

    return (
        EventInvite.objects.filter(
            invitee=user, status=InviteStatus.PENDING, event__is_deleted=False
        )
        .select_related("event", "event__host", "event__start_location")
        .order_by("created_at")
    )


# PHASE 3 SELECTORS


def get_event_detail(slug):
    """
    Get event with all related data for detail page

    Returns:
        Event object with prefetched relationships
    """
    from .models import Event

    return (
        Event.objects.select_related("host", "start_location")
        .prefetch_related("locations__location", "memberships__user")
        .get(slug=slug, is_deleted=False)
    )


def user_role_in_event(event, user):
    """
    Determine user's role in event

    Returns:
        'HOST' | 'ATTENDEE' | 'VISITOR'
    """
    from .models import EventMembership
    from .enums import MembershipRole

    if event.host == user:
        return "HOST"

    membership = EventMembership.objects.filter(
        event=event, user=user, role__in=[MembershipRole.ATTENDEE]
    ).first()

    if membership:
        return "ATTENDEE"

    return "VISITOR"


def list_event_attendees(event):
    """
    Get all attendees (HOST + ATTENDEE roles)

    Returns:
        QuerySet of EventMembership objects with user info
    """
    from .models import EventMembership
    from .enums import MembershipRole

    return (
        EventMembership.objects.filter(
            event=event, role__in=[MembershipRole.HOST, MembershipRole.ATTENDEE]
        )
        .select_related("user")
        .order_by("joined_at")
    )


def list_chat_messages(event, limit=20):
    """
    Get latest chat messages for event

    Args:
        event: Event object
        limit: Max messages to return (default 20)

    Returns:
        List of EventChatMessage ordered oldest first
    """
    from .models import EventChatMessage

    # Get latest N messages in descending order, then reverse to oldest-first
    messages = list(
        EventChatMessage.objects.filter(event=event)
        .select_related("author")
        .order_by("-created_at")[:limit]
    )
    return messages[::-1]  # Reverse to show oldest first


def get_join_request(event, user):
    """
    Get user's pending join request for event (if exists)

    Returns:
        EventJoinRequest or None
    """
    from .models import EventJoinRequest
    from .enums import JoinRequestStatus

    return EventJoinRequest.objects.filter(
        event=event, requester=user, status=JoinRequestStatus.PENDING
    ).first()


def list_pending_join_requests(event):
    """
    Get pending join requests for event (host only)

    Returns:
        QuerySet of EventJoinRequest objects
    """
    from .models import EventJoinRequest
    from .enums import JoinRequestStatus

    return (
        EventJoinRequest.objects.filter(event=event, status=JoinRequestStatus.PENDING)
        .select_related("requester")
        .order_by("created_at")
    )
