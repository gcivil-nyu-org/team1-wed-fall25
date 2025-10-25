from django.db import models
from django.contrib.auth.models import User
from django.utils.html import mark_safe


class PublicArt(models.Model):
    """Model for NYC Public Design Commission Outdoor Public Art"""

    # Basic Information
    artist_name = models.CharField(max_length=500, blank=True, null=True)
    title = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="", blank=True, null=True)

    def art_image(self):
        return mark_safe(
            '<img style="border: 1px solid #333; object-fit: contain;" src="{url}" width="500px" height="500px" />'.format(  # noqa E501
                url=self.image.url,
            )
        )

    # Location Information
    location = models.CharField(max_length=500, blank=True, null=True)
    borough = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True
    )

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
        ordering = ["title"]

    def __str__(self):
        return f"{self.title or 'Untitled'} by {self.artist_name or 'Unknown'}"


class UserFavoriteArt(models.Model):
    """Track user's favorite art pieces"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorite_art"
    )
    art = models.ForeignKey(
        PublicArt, on_delete=models.CASCADE, related_name="favorited_by"
    )
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ["user", "art"]
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} - {self.art.title}"


class ArtComment(models.Model):
    """User comments on art pieces"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="art_comments"
    )
    art = models.ForeignKey(
        PublicArt, on_delete=models.CASCADE, related_name="comments"
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} on {self.art.title}"


# class Photo(models.Model):
#     image = models.ImageField(upload_to='photos/')
