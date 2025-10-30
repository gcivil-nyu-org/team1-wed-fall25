import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify

from loc_detail.models import PublicArt
from .enums import (
    EventVisibility,
    MembershipRole,
    InviteStatus,
    JoinRequestStatus,
    MessageReportReason,
    ReportStatus,
)


class Event(models.Model):
    """Core event model"""

    slug = models.SlugField(unique=True, max_length=100, db_index=True)
    title = models.CharField(max_length=80)
    host = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="hosted_events"
    )
    visibility = models.CharField(
        max_length=20,
        choices=EventVisibility.choices,
        default=EventVisibility.PUBLIC_OPEN,
    )
    start_time = models.DateTimeField(db_index=True)
    start_location = models.ForeignKey(
        PublicArt, on_delete=models.PROTECT, related_name="events"
    )
    description = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["start_time"]),
            models.Index(fields=["visibility"]),
            models.Index(fields=["host", "start_time"]),
        ]
        ordering = ["-start_time"]

    def __str__(self):
        return f"{self.title} by {self.host.username}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:50]
            unique_id = str(uuid.uuid4())[:8]
            self.slug = f"{base_slug}-{unique_id}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("events:detail", kwargs={"slug": self.slug})


class EventLocation(models.Model):
    """Ordered itinerary stops beyond the starting location"""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="locations")
    location = models.ForeignKey(PublicArt, on_delete=models.PROTECT)
    order = models.PositiveSmallIntegerField()
    note = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "order"], name="uniq_event_location_order"
            ),
            models.UniqueConstraint(
                fields=["event", "location"], name="uniq_event_location_pair"
            ),
        ]
        ordering = ["order"]

    def __str__(self):
        return f"{self.event.title} - Stop {self.order}"


class EventMembership(models.Model):
    """Tracks who is in the event and their role"""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="event_memberships"
    )
    role = models.CharField(max_length=20, choices=MembershipRole.choices)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"], name="uniq_event_user_membership"
            )
        ]
        indexes = [
            models.Index(fields=["event", "role"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.role} at {self.event.title}"


class EventInvite(models.Model):
    """Tracks invite lifecycle"""

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="invites")
    invited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="sent_invites"
    )
    invitee = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="event_invitations"
    )
    status = models.CharField(
        max_length=20, choices=InviteStatus.choices, default=InviteStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "invitee"], name="uniq_event_invitee"
            )
        ]
        indexes = [
            models.Index(fields=["invitee", "status"]),
            models.Index(fields=["event"]),
        ]

    def __str__(self):
        return f"Invite to {self.invitee.username} for {self.event.title}"


class EventChatMessage(models.Model):
    """Chat messages for event attendees (Phase 3)"""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="chat_messages"
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["event", "-created_at"]),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.username}: {self.message[:50]}"


class EventJoinRequest(models.Model):
    """Visitors requesting to join PUBLIC_INVITE events (Phase 3)"""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="join_requests"
    )
    requester = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=JoinRequestStatus.choices,
        default=JoinRequestStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "requester"], name="uniq_event_join_request"
            )
        ]
        indexes = [
            models.Index(fields=["event", "status"]),
            models.Index(fields=["requester"]),
        ]

    def __str__(self):
        return f"Join request by {self.requester.username} for {self.event.title}"


class EventFavorite(models.Model):
    """Tracks user's favorited events"""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="favorited_by"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorite_events"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"], name="uniq_event_favorite"
            )
        ]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["event"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} favorited {self.event.title}"


class MessageReport(models.Model):
    """Reports for inappropriate chat messages"""

    message = models.ForeignKey(
        EventChatMessage, on_delete=models.CASCADE, related_name="reports"
    )
    reporter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="message_reports"
    )
    reason = models.CharField(max_length=20, choices=MessageReportReason.choices)
    description = models.TextField(blank=True, max_length=500)
    status = models.CharField(
        max_length=20, choices=ReportStatus.choices, default=ReportStatus.PENDING
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_message_reports",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message", "reporter"], name="uniq_message_report"
            )
        ]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["message"]),
            models.Index(fields=["reporter"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report on {self.message.id} by {self.reporter.username}"


class DirectChat(models.Model):
    """1-on-1 chat between two users within an event"""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="direct_chats"
    )
    user1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="direct_chats_initiated"
    )
    user2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="direct_chats_received"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user1", "user2"], name="uniq_direct_chat"
            )
        ]
        indexes = [
            models.Index(fields=["user1", "-updated_at"]),
            models.Index(fields=["user2", "-updated_at"]),
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        u1, u2 = self.user1.username, self.user2.username
        event_title = self.event.title
        return f"Chat between {u1} and {u2} in {event_title}"

    def get_other_user(self, user):
        """Get the other user in this chat"""
        return self.user2 if self.user1 == user else self.user1

    def has_user_left(self, user):
        """Check if a user has left this chat"""
        from .models import DirectChatLeave

        return DirectChatLeave.objects.filter(chat=self, user=user).exists()

    def get_active_users(self):
        """Get users who haven't left this chat"""
        from .models import DirectChatLeave

        left_users = set(
            DirectChatLeave.objects.filter(chat=self).values_list("user", flat=True)
        )
        return (
            [self.user1, self.user2]
            if not left_users
            else [u for u in [self.user1, self.user2] if u.id not in left_users]
        )


class DirectMessage(models.Model):
    """Messages in 1-on-1 chat"""

    chat = models.ForeignKey(
        DirectChat, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["chat", "-created_at"]),
            models.Index(fields=["sender"]),
            models.Index(fields=["is_read"]),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"


class DirectChatLeave(models.Model):
    """Track when users leave a direct chat"""

    chat = models.ForeignKey(
        DirectChat, on_delete=models.CASCADE, related_name="leaves"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_leaves")
    left_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["chat", "user"], name="uniq_chat_leave")
        ]
        indexes = [
            models.Index(fields=["user", "-left_at"]),
        ]
        ordering = ["-left_at"]

    def __str__(self):
        return f"{self.user.username} left chat {self.chat.id}"
