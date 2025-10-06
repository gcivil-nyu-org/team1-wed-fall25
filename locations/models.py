from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Tag(models.Model):
    """Tags/categories for locations (e.g., murals, sculptures, parks)"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    category = models.CharField(max_length=50, blank=True, help_text="Optional grouping")
    
    class Meta:
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Location(models.Model):
    """Art venue/location model"""
    SOURCE_CHOICES = [
        ('seeded', 'Seeded from NYC Open Data'),
        ('user', 'User-contributed'),
    ]
    
    # Basic info
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True)
    
    # Address
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, default='New York')
    state = models.CharField(max_length=50, default='NY')
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='USA')
    
    # Geolocation
    latitude = models.DecimalField(max_digits=9, decimal_places=6, db_index=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, db_index=True)
    
    # Media
    website_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True, help_text="External image URL")
    
    # Source tracking
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='user')
    source_id = models.CharField(max_length=100, blank=True, help_text="ID from external source")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='locations_created')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Aggregated ratings (denormalized for performance)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    review_count = models.IntegerField(default=0)
    
    # Relationships
    tags = models.ManyToManyField(Tag, blank=True, related_name='locations')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['source', 'source_id']),
        ]
    
    def __str__(self):
        return self.name
    
    def update_rating(self):
        """Recalculate average rating from reviews"""
        from django.db.models import Avg, Count
        from reviews.models import Review
        
        stats = Review.objects.filter(location=self).aggregate(
            avg=Avg('rating'),
            count=Count('id')
        )
        self.average_rating = stats['avg'] or 0.0
        self.review_count = stats['count']
        self.save(update_fields=['average_rating', 'review_count'])


class Favorite(models.Model):
    """User favorites"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'location']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} → {self.location.name}"
