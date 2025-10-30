from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.utils.html import mark_safe, format_html


class PublicArt(models.Model):
    """Model for NYC Public Design Commission Outdoor Public Art"""

    # Basic Information
    artist_name = models.CharField(max_length=500, blank=True, null=True)
    title = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="", blank=True, null=True)

    def art_image(self):
        return mark_safe(
            (
                '<img style="border: 1px solid #333; object-fit: contain;" '
                'src="{url}" width="500px" height="500px" />'
            ).format(url=self.image.url)
        )

    def get_image_status(self):
        if self.image:
            return format_html("&#9989;")
        else:
            return "-"

    get_image_status.short_description = "Has image"

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

    def get_average_rating(self):
        """Calculate average rating from all reviews (not replies)"""
        avg = self.comments.filter(parent__isnull=True).aggregate(Avg("rating"))[
            "rating__avg"
        ]
        return round(avg, 1) if avg else 0

    def get_total_reviews(self):
        """Get total number of reviews (not replies)"""
        return self.comments.filter(parent__isnull=True).count()


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
    """User reviews/comments on art pieces with ratings"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="art_comments"
    )
    art = models.ForeignKey(
        PublicArt, on_delete=models.CASCADE, related_name="comments"
    )
    comment = models.TextField()
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        default=5,
        help_text="Rating from 1 to 5 stars",
    )
    # Image upload for reviews
    image = models.ImageField(
        upload_to="review_images/",
        blank=True,
        null=True,
        help_text="Upload a photo of the artwork",
    )
    # For threading/replies
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} on {self.art.title}"

    @property
    def likes_count(self):
        """Get total likes for this comment"""
        return self.likes.filter(is_like=True).count()

    @property
    def dislikes_count(self):
        """Get total dislikes for this comment"""
        return self.likes.filter(is_like=False).count()

    def user_reaction(self, user):
        """Check if user has liked/disliked this comment"""
        reaction = self.likes.filter(user=user).first()
        if reaction:
            return "like" if reaction.is_like else "dislike"
        return None


class CommentLike(models.Model):
    """Track likes/dislikes on comments"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comment_reactions"
    )
    comment = models.ForeignKey(
        ArtComment, on_delete=models.CASCADE, related_name="likes"
    )
    is_like = models.BooleanField(default=True)  # True for like, False for dislike
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "comment"]
        ordering = ["-created_at"]

    def __str__(self):
        reaction = "liked" if self.is_like else "disliked"
        return (
            f"{self.user.username} {reaction} comment by {self.comment.user.username}"
        )
