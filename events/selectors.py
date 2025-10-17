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

