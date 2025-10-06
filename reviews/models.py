from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from locations.models import Location


class Review(models.Model):
    """Review of a location"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    text = models.TextField(help_text="Your review")
    is_flagged = models.BooleanField(default=False, help_text="Flagged for moderation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        # One review per user per location
        unique_together = ['user', 'location']
    
    def __str__(self):
        return f"{self.user.username} - {self.location.name} ({self.rating}★)"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update location rating
        self.location.update_rating()


class ReviewPhoto(models.Model):
    """Photos attached to reviews"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='review_photos/%Y/%m/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Photo for review #{self.review.pk}"
