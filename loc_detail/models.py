from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.utils.html import mark_safe, format_html

from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image
from os.path import splitext


class PublicArt(models.Model):
    """Model for NYC Public Design Commission Outdoor Public Art"""

    # Basic Information
    artist_name = models.CharField(max_length=500, blank=True, null=True)
    title = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="", blank=True, null=True)
    thumbnail = models.ImageField(upload_to="", blank=True, null=True, editable=False)

    THUMBNAIL_SIZE = (300, 300)
    MAX_IMAGE_SIZE = (2000, 2000)
    MAX_IMAGE_QUALITY = 85

    def make_thumbnail(self, image_field, size=THUMBNAIL_SIZE):
        if not image_field:
            return None
        try:
            img = Image.open(image_field)
            img = img.convert("RGB")
            img.thumbnail(size, Image.LANCZOS)

            thumb_io = BytesIO()
            img.save(thumb_io, format="JPEG", quality=85)
            base_name = (
                getattr(image_field, "name", "thumb").split("/")[-1].rsplit(".", 1)[0]
            )
            thumb_name = f"thumb_{base_name}.jpg"
            return ContentFile(thumb_io.getvalue(), name=thumb_name)
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None

    def downsample_image(
        self, image_field, max_size=MAX_IMAGE_SIZE, quality=MAX_IMAGE_QUALITY
    ):
        if not image_field:
            return None
        try:
            image_field.open()
            img = Image.open(image_field)
            img_format = img.format or "JPEG"
            if img.width <= max_size[0] and img.height <= max_size[1]:
                return None

            img = img.convert("RGB")
            img.thumbnail(max_size, Image.LANCZOS)

            out_io = BytesIO()
            save_format = (
                "JPEG"
                if img_format.upper() not in ("PNG", "GIF", "WEBP")
                else img_format
            )
            img.save(out_io, format=save_format, quality=quality)
            base, _ = splitext(getattr(image_field, "name", "image"))
            new_name = f"{base}_resized.jpg"
            return ContentFile(out_io.getvalue(), name=new_name)
        except Exception:
            return None

    def save(self, *args, **kwargs):
        image_changed = False
        if self.pk:
            try:
                old = PublicArt.objects.get(pk=self.pk)
                if bool(old.image) != bool(self.image) or (
                    old.image and self.image and old.image.name != self.image.name
                ):
                    image_changed = True
            except PublicArt.DoesNotExist:
                image_changed = True
        else:
            image_changed = bool(self.image)

        if self.image and image_changed:
            downsampled = self.downsample_image(self.image)
            if downsampled:
                self.image.save(downsampled.name, downsampled, save=False)

        if self.image and image_changed:
            thumb_file = self.make_thumbnail(self.image)
            if thumb_file:
                try:
                    if self.pk:
                        old = PublicArt.objects.get(pk=self.pk)
                        if (
                            old.thumbnail
                            and old.thumbnail.name
                            and old.thumbnail.storage.exists(old.thumbnail.name)
                        ):
                            old.thumbnail.storage.delete(old.thumbnail.name)
                except Exception:
                    pass
                self.thumbnail.save(thumb_file.name, thumb_file, save=False)

        if not self.image and self.thumbnail:
            try:
                if self.thumbnail.name and self.thumbnail.storage.exists(
                    self.thumbnail.name
                ):
                    self.thumbnail.storage.delete(self.thumbnail.name)
            except Exception:
                pass
            self.thumbnail = None

        super().save(*args, **kwargs)

    def art_image(self):
        return mark_safe(
            (
                '<img style="border: 1px solid #ccc;'
                'object-fit: contain; max-width: 100%; max-height: 500px;"'
                'src="{url}"  />'
            ).format(url=self.image.url)
        )

    def art_thumbnail(self):
        if self.thumbnail:
            return mark_safe(('<img src="{url}" />').format(url=self.thumbnail.url))
        return "No Thumbnail"

    def square_thumbnail(self):
        if self.thumbnail:
            return mark_safe(
                ('<img class="art-thumbnail" src="{url}" />').format(
                    url=self.thumbnail.url
                )
            )
        return "No Thumbnail"

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

    external_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Public Art"
        verbose_name_plural = "Public Art Pieces"
        ordering = ["title"]

    def __str__(self):
        return f"{self.title or 'Untitled'} by {self.artist_name or 'Unknown'}"

    def get_average_rating(self):
        avg = self.comments.filter(parent__isnull=True).aggregate(Avg("rating"))[
            "rating__avg"
        ]
        return round(avg, 1) if avg else 0

    def get_total_reviews(self):
        return self.comments.filter(parent__isnull=True).count()


class UserFavoriteArt(models.Model):
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
        return self.likes.filter(is_like=True).count()

    @property
    def dislikes_count(self):
        return self.likes.filter(is_like=False).count()

    def user_reaction(self, user):
        reaction = self.likes.filter(user=user).first()
        if reaction:
            return "like" if reaction.is_like else "dislike"
        return None


class CommentImage(models.Model):
    """Multiple images for comments"""

    comment = models.ForeignKey(
        ArtComment, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="review_images/", help_text="Review photo")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "uploaded_at"]

    def __str__(self):
        return f"Image for comment by {self.comment.user.username}"

    def delete(self, *args, **kwargs):
        """Delete the image file when the model instance is deleted"""
        if self.image:
            storage = self.image.storage
            if storage.exists(self.image.name):
                storage.delete(self.image.name)
        super().delete(*args, **kwargs)


class CommentLike(models.Model):
    """Track likes/dislikes on comments"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comment_reactions"
    )
    comment = models.ForeignKey(
        ArtComment, on_delete=models.CASCADE, related_name="likes"
    )
    is_like = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "comment"]
        ordering = ["-created_at"]

    def __str__(self):
        reaction = "liked" if self.is_like else "disliked"
        return (
            f"{self.user.username} {reaction} comment by {self.comment.user.username}"
        )


class CommentReport(models.Model):
    """Reports on comments"""

    REPORT_REASONS = [
        ("spam", "Spam or misleading"),
        ("harassment", "Harassment or bullying"),
        ("hate", "Hate speech or discrimination"),
        ("violence", "Violence or dangerous content"),
        ("sexual", "Sexual content"),
        ("misinformation", "False information"),
        ("copyright", "Copyright violation"),
        ("personal", "Personal information shared"),
        ("other", "Other (please specify)"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("reviewing", "Under Review"),
        ("resolved", "Resolved"),
        ("dismissed", "Dismissed"),
    ]

    comment = models.ForeignKey(
        ArtComment, on_delete=models.CASCADE, related_name="reports"
    )
    reporter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comment_reports"
    )
    reasons = models.JSONField(help_text="List of selected report reasons")
    additional_info = models.TextField(
        blank=True, help_text="Additional details about the report"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_reports",
    )
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["comment", "reporter"]

    def __str__(self):
        return f"Report by {self.reporter.username} on comment {self.comment.id}"
