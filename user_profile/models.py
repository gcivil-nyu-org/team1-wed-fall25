from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile with additional information"""

    PRIVACY_CHOICES = [
        ("PUBLIC", "Public"),
        ("PRIVATE", "Private"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=200, blank=True)
    about = models.TextField(max_length=500, blank=True)
    contact_info = models.CharField(max_length=200, blank=True)
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default="PUBLIC")
    profile_image = models.ImageField(
        upload_to="profile_images/", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_hosted_events_count(self):
        """Get count of public events hosted by user"""
        from events.models import Event
        from events.enums import EventVisibility

        return Event.objects.filter(
            host=self.user,
            is_deleted=False,
            visibility__in=[EventVisibility.PUBLIC_OPEN, EventVisibility.PUBLIC_INVITE],
        ).count()

    def is_public(self):
        """Check if profile is public"""
        return self.privacy == "PUBLIC"


class UserFollow(models.Model):
    """Track user follow relationships"""

    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following"
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "following")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create profile when user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save profile when user is saved"""
    if hasattr(instance, "profile"):
        instance.profile.save()
