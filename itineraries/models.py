from django.db import models
from django.contrib.auth.models import User
from locations.models import Location
import secrets


class Itinerary(models.Model):
    """User's itinerary/route"""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='itineraries')
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True, help_text="Personal notes about this itinerary")
    is_public = models.BooleanField(default=False, help_text="Make visible to others")
    share_token = models.CharField(max_length=32, blank=True, unique=True, 
                                     help_text="Token for sharing via link")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = 'Itineraries'
    
    def __str__(self):
        return f"{self.owner.username} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)
    
    def get_ordered_items(self):
        """Get items in order"""
        return self.items.all().select_related('location').order_by('order_index')


class ItineraryItem(models.Model):
    """Individual location in an itinerary"""
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='items')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='itinerary_items')
    order_index = models.PositiveIntegerField(default=0, help_text="Order in the itinerary")
    note = models.TextField(blank=True, help_text="Personal note for this stop")
    planned_start = models.DateTimeField(null=True, blank=True, help_text="Planned arrival time")
    planned_end = models.DateTimeField(null=True, blank=True, help_text="Planned departure time")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order_index', 'created_at']
        unique_together = ['itinerary', 'location']
    
    def __str__(self):
        return f"{self.itinerary.title} - {self.order_index}: {self.location.name}"
