from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from locations.models import Location
from itineraries.models import Itinerary
import secrets


class Event(models.Model):
    """Public or private art events"""
    VISIBILITY_CHOICES = [
        ('public', 'Public - Anyone can view and join'),
        ('restricted', 'Restricted - Invitation only'),
        ('private', 'Private - Only owner'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events_owned')
    title = models.CharField(max_length=200)
    description = models.TextField()
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    max_attendees = models.PositiveIntegerField(null=True, blank=True, 
                                                  help_text="Leave blank for unlimited")
    share_token = models.CharField(max_length=32, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    itinerary = models.ForeignKey(Itinerary, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='events', help_text="Optional linked itinerary")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.title} - {self.start_time.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)
    
    def attendee_count(self):
        return self.rsvps.filter(status='going').count()
    
    def is_full(self):
        if not self.max_attendees:
            return False
        return self.attendee_count() >= self.max_attendees


class EventLocation(models.Model):
    """Locations in an event (single or multi-stop)"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='locations')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='events')
    order_index = models.PositiveIntegerField(default=0)
    note = models.TextField(blank=True, help_text="Note for this stop")
    
    class Meta:
        ordering = ['order_index']
        unique_together = ['event', 'location']
    
    def __str__(self):
        return f"{self.event.title} - {self.location.name}"


class Invitation(models.Model):
    """Event invitations"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    
    ROLE_CHOICES = [
        ('attendee', 'Attendee'),
        ('cohost', 'Co-host'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invitations')
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invitations_sent')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='invitations_received')
    invited_email = models.EmailField(blank=True, help_text="For non-registered users")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='attendee')
    token = models.CharField(max_length=32, unique=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        target = self.invited_user.username if self.invited_user else self.invited_email
        return f"{self.event.title} → {target}"
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(24)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at


class RSVP(models.Model):
    """User RSVP status for events"""
    STATUS_CHOICES = [
        ('going', 'Going'),
        ('maybe', 'Maybe'),
        ('not_going', 'Not Going'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rsvps')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='going')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['event', 'user']
    
    def __str__(self):
        return f"{self.user.username} → {self.event.title} ({self.status})"
