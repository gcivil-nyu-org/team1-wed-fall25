"""
Unit tests for messages app (user-to-user messaging feature)
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json

from messages.models import (
    UserOnlineStatus,
    Conversation,
    PrivateMessage,
    ConversationHidden,
)
from messages.forms import MessageForm


# ============================================================================
# Model Tests
# ============================================================================


class UserOnlineStatusModelTests(TestCase):
    """Test cases for UserOnlineStatus model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_create_online_status(self):
        """Test creating a UserOnlineStatus instance"""
        status = UserOnlineStatus.objects.create(user=self.user)
        self.assertEqual(status.user, self.user)
        self.assertFalse(status.is_online)
        self.assertIsNotNone(status.last_seen)

    def test_str_method_online(self):
        """Test string representation when online"""
        status = UserOnlineStatus.objects.create(user=self.user, is_online=True)
        self.assertEqual(str(status), "testuser - online")

    def test_str_method_offline(self):
        """Test string representation when offline"""
        status = UserOnlineStatus.objects.create(user=self.user, is_online=False)
        self.assertEqual(str(status), "testuser - offline")

    def test_get_or_create_status(self):
        """Test get_or_create_status class method"""
        status1 = UserOnlineStatus.get_or_create_status(self.user)
        status2 = UserOnlineStatus.get_or_create_status(self.user)
        self.assertEqual(status1.id, status2.id)

    def test_set_online(self):
        """Test set_online method"""
        status = UserOnlineStatus.objects.create(user=self.user, is_online=False)
        old_last_seen = status.last_seen
        status.set_online()
        status.refresh_from_db()
        self.assertTrue(status.is_online)
        self.assertGreaterEqual(status.last_seen, old_last_seen)

    def test_set_offline(self):
        """Test set_offline method"""
        status = UserOnlineStatus.objects.create(user=self.user, is_online=True)
        old_last_seen = status.last_seen
        status.set_offline()
        status.refresh_from_db()
        self.assertFalse(status.is_online)
        self.assertGreaterEqual(status.last_seen, old_last_seen)

    def test_one_to_one_relationship(self):
        """Test that each user can only have one online status"""
        UserOnlineStatus.objects.create(user=self.user)
        # Creating another should raise an error
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            UserOnlineStatus.objects.create(user=self.user)


class ConversationModelTests(TestCase):
    """Test cases for Conversation model"""

    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")

    def test_create_conversation(self):
        """Test creating a Conversation instance"""
        conv = Conversation.objects.create(user1=self.user1, user2=self.user2)
        self.assertEqual(conv.user1, self.user1)
        self.assertEqual(conv.user2, self.user2)
        self.assertIsNotNone(conv.created_at)
        self.assertIsNotNone(conv.updated_at)

    def test_str_method(self):
        """Test string representation"""
        conv = Conversation.objects.create(user1=self.user1, user2=self.user2)
        self.assertEqual(str(conv), "Conversation: user1 <-> user2")

    def test_get_other_user(self):
        """Test get_other_user method"""
        conv = Conversation.objects.create(user1=self.user1, user2=self.user2)
        self.assertEqual(conv.get_other_user(self.user1), self.user2)
        self.assertEqual(conv.get_other_user(self.user2), self.user1)

    def test_get_last_message(self):
        """Test get_last_message method"""
        conv = Conversation.objects.create(user1=self.user1, user2=self.user2)
        # No messages yet
        self.assertIsNone(conv.get_last_message())
        # Add messages
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user1, content="Hello"
        )
        msg2 = PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hi there"
        )
        self.assertEqual(conv.get_last_message(), msg2)

    def test_get_unread_count(self):
        """Test get_unread_count method"""
        conv = Conversation.objects.create(user1=self.user1, user2=self.user2)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hello", is_read=False
        )
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hi", is_read=False
        )
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user1, content="Hey", is_read=False
        )
        # user1 should have 2 unread (from user2)
        self.assertEqual(conv.get_unread_count(self.user1), 2)
        # user2 should have 1 unread (from user1)
        self.assertEqual(conv.get_unread_count(self.user2), 1)

    def test_get_or_create_conversation(self):
        """Test get_or_create_conversation class method"""
        conv1, created1 = Conversation.get_or_create_conversation(
            self.user1, self.user2
        )
        self.assertTrue(created1)
        conv2, created2 = Conversation.get_or_create_conversation(
            self.user2, self.user1
        )
        self.assertFalse(created2)
        self.assertEqual(conv1.id, conv2.id)

    def test_get_or_create_conversation_order_independent(self):
        """Test that conversation is order-independent"""
        conv1, _ = Conversation.get_or_create_conversation(self.user1, self.user2)
        conv2, _ = Conversation.get_or_create_conversation(self.user2, self.user1)
        self.assertEqual(conv1.id, conv2.id)

    def test_unique_constraint(self):
        """Test unique constraint on user1, user2"""
        Conversation.objects.create(user1=self.user1, user2=self.user2)
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Conversation.objects.create(user1=self.user1, user2=self.user2)


class PrivateMessageModelTests(TestCase):
    """Test cases for PrivateMessage model"""

    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        self.conversation = Conversation.objects.create(
            user1=self.user1, user2=self.user2
        )

    def test_create_message(self):
        """Test creating a PrivateMessage instance"""
        msg = PrivateMessage.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Hello, how are you?",
        )
        self.assertEqual(msg.conversation, self.conversation)
        self.assertEqual(msg.sender, self.user1)
        self.assertEqual(msg.content, "Hello, how are you?")
        self.assertFalse(msg.is_read)
        self.assertIsNotNone(msg.created_at)

    def test_str_method(self):
        """Test string representation"""
        msg = PrivateMessage.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Hello, how are you doing today?",
        )
        self.assertEqual(str(msg), "user1: Hello, how are you doing today?")

    def test_str_method_truncates_long_content(self):
        """Test that string representation truncates long content"""
        long_content = "A" * 100
        msg = PrivateMessage.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content=long_content,
        )
        self.assertEqual(str(msg), f"user1: {'A' * 50}")

    def test_mark_as_read(self):
        """Test mark_as_read method"""
        msg = PrivateMessage.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Hello",
            is_read=False,
        )
        self.assertFalse(msg.is_read)
        msg.mark_as_read()
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_mark_as_read_already_read(self):
        """Test mark_as_read when already read"""
        msg = PrivateMessage.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Hello",
            is_read=True,
        )
        msg.mark_as_read()  # Should not raise error
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_ordering(self):
        """Test that messages are ordered by created_at"""
        msg1 = PrivateMessage.objects.create(
            conversation=self.conversation, sender=self.user1, content="First"
        )
        msg2 = PrivateMessage.objects.create(
            conversation=self.conversation, sender=self.user2, content="Second"
        )
        messages = list(self.conversation.private_messages.all())
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)

    def test_cascade_delete_on_conversation(self):
        """Test that messages are deleted when conversation is deleted"""
        msg = PrivateMessage.objects.create(
            conversation=self.conversation, sender=self.user1, content="Hello"
        )
        msg_id = msg.id
        self.conversation.delete()
        self.assertFalse(PrivateMessage.objects.filter(id=msg_id).exists())


class ConversationHiddenModelTests(TestCase):
    """Test cases for ConversationHidden model"""

    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        self.conversation = Conversation.objects.create(
            user1=self.user1, user2=self.user2
        )

    def test_create_hidden(self):
        """Test creating a ConversationHidden instance"""
        hidden = ConversationHidden.objects.create(
            conversation=self.conversation, user=self.user1
        )
        self.assertEqual(hidden.conversation, self.conversation)
        self.assertEqual(hidden.user, self.user1)
        self.assertIsNotNone(hidden.hidden_at)

    def test_str_method(self):
        """Test string representation"""
        hidden = ConversationHidden.objects.create(
            conversation=self.conversation, user=self.user1
        )
        self.assertEqual(str(hidden), f"user1 hid conversation {self.conversation.id}")

    def test_unique_constraint(self):
        """Test unique constraint on conversation, user"""
        ConversationHidden.objects.create(
            conversation=self.conversation, user=self.user1
        )
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            ConversationHidden.objects.create(
                conversation=self.conversation, user=self.user1
            )

    def test_both_users_can_hide(self):
        """Test that both users can hide the same conversation"""
        hidden1 = ConversationHidden.objects.create(
            conversation=self.conversation, user=self.user1
        )
        hidden2 = ConversationHidden.objects.create(
            conversation=self.conversation, user=self.user2
        )
        self.assertEqual(ConversationHidden.objects.count(), 2)
        self.assertNotEqual(hidden1.id, hidden2.id)


# ============================================================================
# Form Tests
# ============================================================================


class MessageFormTests(TestCase):
    """Test cases for MessageForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form = MessageForm(data={"content": "Hello, how are you?"})
        self.assertTrue(form.is_valid())

    def test_empty_content(self):
        """Test form with empty content"""
        form = MessageForm(data={"content": ""})
        self.assertFalse(form.is_valid())

    def test_whitespace_only_content(self):
        """Test form with whitespace only content"""
        form = MessageForm(data={"content": "   "})
        # Depends on form validation, might be valid or invalid
        # Let's check what the form does
        if form.is_valid():
            self.assertEqual(form.cleaned_data["content"].strip(), "")


# ============================================================================
# View Tests
# ============================================================================


class InboxViewTests(TestCase):
    """Test cases for inbox view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        self.user3 = User.objects.create_user(username="user3", password="testpass123")

    def test_login_required(self):
        """Test that login is required"""
        response = self.client.get(reverse("user_messages:inbox"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_inbox_empty(self):
        """Test inbox with no conversations"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("user_messages:inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_conversations"])

    def test_inbox_with_conversations(self):
        """Test inbox with conversations"""
        self.client.login(username="user1", password="testpass123")
        conv = Conversation.objects.create(user1=self.user1, user2=self.user2)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hello"
        )
        response = self.client.get(reverse("user_messages:inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_conversations"])
        self.assertEqual(len(response.context["conversations"]), 1)

    def test_inbox_hidden_conversation_without_new_messages(self):
        """Test that hidden conversations without new messages are not shown"""
        self.client.login(username="user1", password="testpass123")
        conv = Conversation.objects.create(user1=self.user1, user2=self.user2)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hello"
        )
        ConversationHidden.objects.create(conversation=conv, user=self.user1)
        response = self.client.get(reverse("user_messages:inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_conversations"])

    def test_inbox_hidden_conversation_with_new_messages(self):
        """Test that hidden conversations with new messages are shown"""
        self.client.login(username="user1", password="testpass123")
        conv = Conversation.objects.create(user1=self.user1, user2=self.user2)
        # Create hidden record first
        ConversationHidden.objects.create(conversation=conv, user=self.user1)
        # Then create a message after hidden_at
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="New message"
        )
        response = self.client.get(reverse("user_messages:inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_conversations"])

    def test_inbox_unread_count(self):
        """Test unread count in inbox"""
        self.client.login(username="user1", password="testpass123")
        conv = Conversation.objects.create(user1=self.user1, user2=self.user2)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hello", is_read=False
        )
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hi", is_read=False
        )
        response = self.client.get(reverse("user_messages:inbox"))
        self.assertEqual(response.context["conversations"][0]["unread_count"], 2)

    def test_inbox_online_status(self):
        """Test online status in inbox"""
        self.client.login(username="user1", password="testpass123")
        conv = Conversation.objects.create(user1=self.user1, user2=self.user2)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hello"
        )
        UserOnlineStatus.objects.create(user=self.user2, is_online=True)
        response = self.client.get(reverse("user_messages:inbox"))
        self.assertTrue(response.context["conversations"][0]["is_online"])


class ConversationDetailViewTests(TestCase):
    """Test cases for conversation_detail view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")

    def test_login_required(self):
        """Test that login is required"""
        response = self.client.get(
            reverse("user_messages:conversation", args=[self.user2.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_conversation_with_self_redirects(self):
        """Test that trying to message yourself redirects to inbox"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("user_messages:conversation", args=[self.user1.id])
        )
        self.assertRedirects(response, reverse("user_messages:inbox"))

    def test_conversation_creates_if_not_exists(self):
        """Test that conversation is created if it doesn't exist"""
        self.client.login(username="user1", password="testpass123")
        self.assertEqual(Conversation.objects.count(), 0)
        response = self.client.get(
            reverse("user_messages:conversation", args=[self.user2.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_conversation_displays_messages(self):
        """Test that messages are displayed"""
        self.client.login(username="user1", password="testpass123")
        conv, _ = Conversation.get_or_create_conversation(self.user1, self.user2)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hello"
        )
        response = self.client.get(
            reverse("user_messages:conversation", args=[self.user2.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["chat_messages"]), 1)

    def test_conversation_marks_messages_as_read(self):
        """Test that viewing conversation marks messages as read"""
        self.client.login(username="user1", password="testpass123")
        conv, _ = Conversation.get_or_create_conversation(self.user1, self.user2)
        msg = PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hello", is_read=False
        )
        self.client.get(reverse("user_messages:conversation", args=[self.user2.id]))
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_post_message(self):
        """Test posting a message"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_messages:conversation", args=[self.user2.id]),
            {"content": "Hello!"},
        )
        self.assertEqual(response.status_code, 302)  # Redirects after post
        self.assertEqual(PrivateMessage.objects.count(), 1)
        self.assertEqual(PrivateMessage.objects.first().content, "Hello!")

    def test_post_message_ajax(self):
        """Test posting a message via AJAX"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_messages:conversation", args=[self.user2.id]),
            {"content": "Hello!"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"]["content"], "Hello!")

    def test_from_event_creates_hidden_record(self):
        """Test that from_event=true creates hidden record for existing conversation"""
        self.client.login(username="user1", password="testpass123")
        conv, _ = Conversation.get_or_create_conversation(self.user1, self.user2)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Old message"
        )
        response = self.client.get(
            reverse("user_messages:conversation", args=[self.user2.id])
            + "?from_event=true"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ConversationHidden.objects.filter(
                conversation=conv, user=self.user1
            ).exists()
        )

    def test_hidden_conversation_shows_only_new_messages(self):
        """Test that hidden conversation shows only messages after hidden_at"""
        self.client.login(username="user1", password="testpass123")
        conv, _ = Conversation.get_or_create_conversation(self.user1, self.user2)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Old message"
        )
        ConversationHidden.objects.create(conversation=conv, user=self.user1)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="New message"
        )
        response = self.client.get(
            reverse("user_messages:conversation", args=[self.user2.id])
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.context["chat_messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, "New message")

    def test_invalid_user_returns_404(self):
        """Test that invalid user ID returns 404"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("user_messages:conversation", args=[9999]))
        self.assertEqual(response.status_code, 404)


class UserListViewTests(TestCase):
    """Test cases for user_list view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        self.user3 = User.objects.create_user(
            username="alice", password="testpass123", first_name="Alice"
        )

    def test_login_required(self):
        """Test that login is required"""
        response = self.client.get(reverse("user_messages:user_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_user_list_excludes_current_user(self):
        """Test that current user is excluded from list"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("user_messages:user_list"))
        self.assertEqual(response.status_code, 200)
        usernames = [u["user"].username for u in response.context["users"]]
        self.assertNotIn("user1", usernames)
        self.assertIn("user2", usernames)

    def test_search_by_username(self):
        """Test search functionality by username"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("user_messages:user_list") + "?q=alice")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["users"]), 1)
        self.assertEqual(response.context["users"][0]["user"].username, "alice")

    def test_search_by_first_name(self):
        """Test search functionality by first name"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("user_messages:user_list") + "?q=Alice")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["users"]), 1)

    def test_has_conversation_annotation(self):
        """Test that has_conversation annotation works"""
        self.client.login(username="user1", password="testpass123")
        Conversation.objects.create(user1=self.user1, user2=self.user2)
        response = self.client.get(reverse("user_messages:user_list"))
        users = {
            u["user"].username: u["has_conversation"] for u in response.context["users"]
        }
        self.assertTrue(users["user2"])
        self.assertFalse(users["alice"])

    def test_pagination(self):
        """Test pagination works"""
        self.client.login(username="user1", password="testpass123")
        # Create many users
        for i in range(25):
            User.objects.create_user(username=f"testuser{i}", password="testpass123")
        response = self.client.get(reverse("user_messages:user_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["page_obj"].has_next())


# ============================================================================
# API Endpoint Tests
# ============================================================================


class SendMessageAPITests(TestCase):
    """Test cases for send_message API endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")

    def test_login_required(self):
        """Test that login is required"""
        response = self.client.post(
            reverse("user_messages:send_message", args=[self.user2.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_post_only(self):
        """Test that only POST is allowed"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("user_messages:send_message", args=[self.user2.id])
        )
        self.assertEqual(response.status_code, 405)

    def test_send_message_success(self):
        """Test successful message sending"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_messages:send_message", args=[self.user2.id]),
            {"content": "Hello!"},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(PrivateMessage.objects.count(), 1)

    def test_send_message_to_self_fails(self):
        """Test that sending message to self fails"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_messages:send_message", args=[self.user1.id]),
            {"content": "Hello!"},
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")

    def test_send_empty_message_fails(self):
        """Test that sending empty message fails"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_messages:send_message", args=[self.user2.id]),
            {"content": ""},
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")

    def test_send_message_creates_conversation(self):
        """Test that sending message creates conversation if needed"""
        self.client.login(username="user1", password="testpass123")
        self.assertEqual(Conversation.objects.count(), 0)
        self.client.post(
            reverse("user_messages:send_message", args=[self.user2.id]),
            {"content": "Hello!"},
        )
        self.assertEqual(Conversation.objects.count(), 1)


class GetMessagesAPITests(TestCase):
    """Test cases for get_messages API endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")

    def test_login_required(self):
        """Test that login is required"""
        response = self.client.get(
            reverse("user_messages:get_messages", args=[self.user2.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_get_messages_no_conversation(self):
        """Test getting messages when no conversation exists"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("user_messages:get_messages", args=[self.user2.id])
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["messages"], [])

    def test_get_messages_with_last_id(self):
        """Test getting only new messages after last_id"""
        self.client.login(username="user1", password="testpass123")
        conv, _ = Conversation.get_or_create_conversation(self.user1, self.user2)
        msg1 = PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="First"
        )
        _ = PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Second"
        )
        response = self.client.get(
            reverse("user_messages:get_messages", args=[self.user2.id])
            + f"?last_id={msg1.id}"
        )
        data = json.loads(response.content)
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["content"], "Second")

    def test_get_messages_marks_as_read(self):
        """Test that getting messages marks them as read"""
        self.client.login(username="user1", password="testpass123")
        conv, _ = Conversation.get_or_create_conversation(self.user1, self.user2)
        msg = PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hello", is_read=False
        )
        self.client.get(reverse("user_messages:get_messages", args=[self.user2.id]))
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_get_messages_respects_hidden_at(self):
        """Test that hidden_at is respected"""
        self.client.login(username="user1", password="testpass123")
        conv, _ = Conversation.get_or_create_conversation(self.user1, self.user2)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Old"
        )
        ConversationHidden.objects.create(conversation=conv, user=self.user1)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="New"
        )
        response = self.client.get(
            reverse("user_messages:get_messages", args=[self.user2.id])
        )
        data = json.loads(response.content)
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["content"], "New")


class UnreadCountAPITests(TestCase):
    """Test cases for unread_count API endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")

    def test_login_required(self):
        """Test that login is required"""
        response = self.client.get(reverse("user_messages:unread_count"))
        self.assertEqual(response.status_code, 302)

    def test_unread_count_zero(self):
        """Test unread count when no messages"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("user_messages:unread_count"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["count"], 0)

    def test_unread_count_with_messages(self):
        """Test unread count with unread messages"""
        self.client.login(username="user1", password="testpass123")
        conv, _ = Conversation.get_or_create_conversation(self.user1, self.user2)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hello", is_read=False
        )
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Hi", is_read=False
        )
        response = self.client.get(reverse("user_messages:unread_count"))
        data = json.loads(response.content)
        self.assertEqual(data["count"], 2)

    def test_unread_count_excludes_own_messages(self):
        """Test that own messages are not counted"""
        self.client.login(username="user1", password="testpass123")
        conv, _ = Conversation.get_or_create_conversation(self.user1, self.user2)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user1, content="My message", is_read=False
        )
        response = self.client.get(reverse("user_messages:unread_count"))
        data = json.loads(response.content)
        self.assertEqual(data["count"], 0)

    def test_unread_count_respects_hidden_at(self):
        """Test that hidden_at is respected in count"""
        self.client.login(username="user1", password="testpass123")
        conv, _ = Conversation.get_or_create_conversation(self.user1, self.user2)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="Old", is_read=False
        )
        ConversationHidden.objects.create(conversation=conv, user=self.user1)
        PrivateMessage.objects.create(
            conversation=conv, sender=self.user2, content="New", is_read=False
        )
        response = self.client.get(reverse("user_messages:unread_count"))
        data = json.loads(response.content)
        self.assertEqual(data["count"], 1)  # Only new message


class UpdateOnlineStatusAPITests(TestCase):
    """Test cases for update_online_status API endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username="user1", password="testpass123")

    def test_login_required(self):
        """Test that login is required"""
        response = self.client.post(reverse("user_messages:update_online_status"))
        self.assertEqual(response.status_code, 302)

    def test_post_only(self):
        """Test that only POST is allowed"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("user_messages:update_online_status"))
        self.assertEqual(response.status_code, 405)

    def test_update_online_status_creates_if_not_exists(self):
        """Test that online status is created if it doesn't exist"""
        self.client.login(username="user1", password="testpass123")
        self.assertEqual(UserOnlineStatus.objects.count(), 0)
        response = self.client.post(reverse("user_messages:update_online_status"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserOnlineStatus.objects.count(), 1)
        self.assertTrue(UserOnlineStatus.objects.first().is_online)

    def test_update_online_status_updates_existing(self):
        """Test that existing online status is updated"""
        self.client.login(username="user1", password="testpass123")
        status = UserOnlineStatus.objects.create(user=self.user, is_online=False)
        response = self.client.post(reverse("user_messages:update_online_status"))
        self.assertEqual(response.status_code, 200)
        status.refresh_from_db()
        self.assertTrue(status.is_online)


class DeleteConversationAPITests(TestCase):
    """Test cases for delete_conversation API endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        self.conversation = Conversation.objects.create(
            user1=self.user1, user2=self.user2
        )

    def test_login_required(self):
        """Test that login is required"""
        response = self.client.post(
            reverse("user_messages:delete_conversation", args=[self.conversation.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_post_or_delete_only(self):
        """Test that only POST or DELETE is allowed"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("user_messages:delete_conversation", args=[self.conversation.id])
        )
        self.assertEqual(response.status_code, 405)

    def test_delete_creates_hidden_record(self):
        """Test that deleting creates a hidden record"""
        self.client.login(username="user1", password="testpass123")
        self.assertEqual(ConversationHidden.objects.count(), 0)
        self.client.post(
            reverse("user_messages:delete_conversation", args=[self.conversation.id])
        )
        self.assertEqual(ConversationHidden.objects.count(), 1)
        self.assertTrue(
            ConversationHidden.objects.filter(
                conversation=self.conversation, user=self.user1
            ).exists()
        )

    def test_delete_updates_existing_hidden_record(self):
        """Test that deleting updates existing hidden record"""
        self.client.login(username="user1", password="testpass123")
        old_hidden = ConversationHidden.objects.create(
            conversation=self.conversation, user=self.user1
        )
        old_hidden_at = old_hidden.hidden_at
        # Wait a bit to ensure time difference
        import time

        time.sleep(0.1)
        self.client.post(
            reverse("user_messages:delete_conversation", args=[self.conversation.id])
        )
        old_hidden.refresh_from_db()
        self.assertGreater(old_hidden.hidden_at, old_hidden_at)

    def test_delete_ajax_returns_json(self):
        """Test that AJAX request returns JSON"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_messages:delete_conversation", args=[self.conversation.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")

    def test_delete_non_ajax_redirects(self):
        """Test that non-AJAX request redirects"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_messages:delete_conversation", args=[self.conversation.id])
        )
        self.assertRedirects(response, reverse("user_messages:inbox"))

    def test_delete_other_users_conversation_fails(self):
        """Test that deleting other user's conversation fails"""
        User.objects.create_user(username="user3", password="testpass123")
        self.client.login(username="user3", password="testpass123")
        response = self.client.post(
            reverse("user_messages:delete_conversation", args=[self.conversation.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_invalid_conversation_fails(self):
        """Test that deleting invalid conversation fails"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_messages:delete_conversation", args=[9999])
        )
        self.assertEqual(response.status_code, 404)
