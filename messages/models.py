from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserOnlineStatus(models.Model):
    """Track user online/offline status"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="online_status"
    )
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "messaging_useronlinestatus"
        verbose_name_plural = "User online statuses"

    def __str__(self):
        status = "online" if self.is_online else "offline"
        return f"{self.user.username} - {status}"

    @classmethod
    def get_or_create_status(cls, user):
        """Get or create online status for a user"""
        status, _ = cls.objects.get_or_create(user=user)
        return status

    def set_online(self):
        """Mark user as online"""
        self.is_online = True
        self.last_seen = timezone.now()
        self.save(update_fields=["is_online", "last_seen"])

    def set_offline(self):
        """Mark user as offline"""
        self.is_online = False
        self.last_seen = timezone.now()
        self.save(update_fields=["is_online", "last_seen"])


class Conversation(models.Model):
    """A conversation between two users (no event required)"""

    user1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="conversations_started"
    )
    user2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="conversations_received"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "messaging_conversation"
        constraints = [
            models.UniqueConstraint(
                fields=["user1", "user2"], name="uniq_conversation_users"
            )
        ]
        indexes = [
            models.Index(fields=["user1", "-updated_at"]),
            models.Index(fields=["user2", "-updated_at"]),
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversation: {self.user1.username} <-> {self.user2.username}"

    def get_other_user(self, user):
        """Get the other participant in the conversation"""
        return self.user2 if self.user1 == user else self.user1

    def get_last_message(self):
        """Get the most recent message in this conversation"""
        return self.private_messages.order_by("-created_at").first()

    def get_unread_count(self, user):
        """Get count of unread messages for a user"""
        return self.private_messages.filter(is_read=False).exclude(sender=user).count()

    @classmethod
    def get_or_create_conversation(cls, user1, user2):
        """Get existing conversation or create a new one (order-independent)"""
        # Always store with lower user id as user1 to ensure uniqueness
        if user1.id > user2.id:
            user1, user2 = user2, user1

        conversation, created = cls.objects.get_or_create(user1=user1, user2=user2)
        return conversation, created


class PrivateMessage(models.Model):
    """Individual message in a conversation"""

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="private_messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_private_messages"
    )
    content = models.TextField(max_length=2000)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "messaging_privatemessage"
        indexes = [
            models.Index(fields=["conversation", "-created_at"]),
            models.Index(fields=["sender", "-created_at"]),
            models.Index(fields=["is_read", "conversation"]),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"

    def mark_as_read(self):
        """Mark the message as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=["is_read"])


class ConversationHidden(models.Model):
    """Track when a user hides/deletes a conversation from their view"""

    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="hidden_by"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="hidden_conversations"
    )
    hidden_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messaging_conversationhidden"
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"], name="uniq_conversation_hidden"
            )
        ]
        indexes = [
            models.Index(fields=["user", "-hidden_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} hid conversation {self.conversation.id}"
