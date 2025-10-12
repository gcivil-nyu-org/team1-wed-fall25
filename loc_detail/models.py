from django.db import models
from django.contrib.auth.models import User


class PublicArt(models.Model):
    """Model for NYC Public Design Commission Outdoor Public Art"""
    
    # Basic Information
    artist_name = models.CharField(max_length=500, blank=True, null=True)
    title = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Location Information
    location = models.CharField(max_length=500, blank=True, null=True)
    borough = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    
    # Art Details
    medium = models.CharField(max_length=300, blank=True, null=True)
    dimensions = models.CharField(max_length=300, blank=True, null=True)
    year_created = models.CharField(max_length=50, blank=True, null=True)
    year_dedicated = models.CharField(max_length=50, blank=True, null=True)
    
    # Administrative
    agency = models.CharField(max_length=200, blank=True, null=True)
    community_board = models.CharField(max_length=100, blank=True, null=True)
    
    # Original data reference
    external_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Public Art"
        verbose_name_plural = "Public Art Pieces"
        ordering = ['title']
    
    def __str__(self):
        return f"{self.title or 'Untitled'} by {self.artist_name or 'Unknown'}"