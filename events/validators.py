from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_future_datetime(value):
    """Ensure event is scheduled in the future"""
    if value <= timezone.now():
        raise ValidationError('Event must be scheduled in the future.')


def validate_max_locations(locations, max_allowed=5):
    """Ensure location count doesn't exceed limit"""
    if len(locations) > max_allowed:
        raise ValidationError(f'Maximum {max_allowed} locations allowed.')

