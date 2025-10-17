from django.db.models import Q
from django.contrib.auth import get_user_model
from loc_detail.models import PublicArt

User = get_user_model()


def search_locations(term, limit=10):
    """Search for art locations by title, artist, or location name"""
    return PublicArt.objects.filter(
        Q(title__icontains=term) | 
        Q(artist_name__icontains=term) | 
        Q(location__icontains=term),
        latitude__isnull=False,
        longitude__isnull=False
    ).values('id', 'title', 'artist_name', 'latitude', 'longitude')[:limit]


def search_users(term, limit=10):
    """Search for users by username or email"""
    return User.objects.filter(
        Q(username__icontains=term) | Q(email__icontains=term)
    ).values('id', 'username')[:limit]


def public_event_pins():
    """Get public event pins for map display"""
    from .models import Event
    from .enums import EventVisibility
    
    return Event.objects.filter(
        visibility__in=[EventVisibility.PUBLIC_OPEN, EventVisibility.PUBLIC_INVITE],
        is_deleted=False
    ).select_related('start_location').values(
        'id', 'slug', 'title',
        'start_location__latitude',
        'start_location__longitude'
    )


def list_public_events(query=None, visibility_filter=None, order='start_time'):
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
        is_deleted=False
    ).select_related('host', 'start_location')
    
    # Search filter
    if query:
        qs = qs.filter(
            Q(title__icontains=query) |
            Q(host__username__icontains=query) |
            Q(start_location__title__icontains=query)
        )
    
    # Visibility filter
    if visibility_filter == 'open':
        qs = qs.filter(visibility=EventVisibility.PUBLIC_OPEN)
    elif visibility_filter == 'invite':
        qs = qs.filter(visibility=EventVisibility.PUBLIC_INVITE)
    
    # Ordering
    return qs.order_by(order)


def user_has_joined(event, user):
    """Check if user has joined event (HOST or ATTENDEE)"""
    from .models import EventMembership
    from .enums import MembershipRole
    
    return EventMembership.objects.filter(
        event=event,
        user=user,
        role__in=[MembershipRole.HOST, MembershipRole.ATTENDEE]
    ).exists()


def list_user_invitations(user):
    """
    Get pending invitations for a user
    
    Returns:
        QuerySet of EventInvite objects with event, host, location prefetched
    """
    from .models import EventInvite
    from .enums import InviteStatus
    
    return EventInvite.objects.filter(
        invitee=user,
        status=InviteStatus.PENDING,
        event__is_deleted=False
    ).select_related(
        'event',
        'event__host',
        'event__start_location'
    ).order_by('created_at')

