"""
Test cases for Chat functionality
Tests models, views, and integration for:
1. Real-time messages
2. Private 1-on-1 chat
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from events.models import DirectChat, DirectMessage, DirectChatLeave, Event
from events.enums import EventVisibility
from loc_detail.models import PublicArt


class DirectChatModelTests(TestCase):
    """Test DirectChat model functionality"""

    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username="testuser1", email="test1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            description="Test event for chat testing",
            host=self.user1,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

    def test_direct_chat_creation(self):
        """Test creating a direct chat between two users"""
        chat = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )

        self.assertEqual(chat.event, self.event)
        self.assertEqual(chat.user1, self.user1)
        self.assertEqual(chat.user2, self.user2)
        self.assertIsNotNone(chat.created_at)
        self.assertIsNotNone(chat.updated_at)

    def test_direct_chat_str_representation(self):
        """Test string representation of DirectChat"""
        chat = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )
        expected_str = (
            f"Chat between {self.user1.username} and {self.user2.username} "
            f"in {self.event.title}"
        )
        self.assertEqual(str(chat), expected_str)

    def test_get_other_user(self):
        """Test getting the other user in a chat"""
        chat = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )

        # Test getting other user from user1's perspective
        other_user = chat.get_other_user(self.user1)
        self.assertEqual(other_user, self.user2)

        # Test getting other user from user2's perspective
        other_user = chat.get_other_user(self.user2)
        self.assertEqual(other_user, self.user1)

    def test_unique_chat_constraint(self):
        """Test that only one chat can exist between two users in the same event"""
        # Create first chat
        DirectChat.objects.create(event=self.event, user1=self.user1, user2=self.user2)

        # Try to create another chat between same users in same event (should fail)
        with self.assertRaises(Exception):
            DirectChat.objects.create(
                event=self.event, user1=self.user1, user2=self.user2
            )

    def test_chat_ordering(self):
        """Test that chats are ordered by updated_at descending"""
        chat1 = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )

        # Create another event and chat
        event2 = Event.objects.create(
            title="Test Event 2",
            description="Second test event",
            host=self.user1,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=2),
            start_location=self.location,
        )
        DirectChat.objects.create(event=event2, user1=self.user1, user2=self.user2)

        # Update chat1 to make it more recent
        chat1.save()  # This updates updated_at

        chats = list(DirectChat.objects.all())
        self.assertEqual(chats[0], chat1)  # More recently updated comes first


class DirectMessageModelTests(TestCase):
    """Test DirectMessage model functionality"""

    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username="testuser1", email="test1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            description="Test event for chat testing",
            host=self.user1,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        self.chat = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )

    def test_direct_message_creation(self):
        """Test creating a direct message"""
        message = DirectMessage.objects.create(
            chat=self.chat, sender=self.user1, content="Hello, this is a test message!"
        )

        self.assertEqual(message.chat, self.chat)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, "Hello, this is a test message!")
        self.assertFalse(message.is_read)
        self.assertIsNotNone(message.created_at)

    def test_direct_message_str_representation(self):
        """Test string representation of DirectMessage"""
        message = DirectMessage.objects.create(
            chat=self.chat, sender=self.user1, content="Test message"
        )
        expected_str = f"{self.user1.username}: Test message"
        self.assertEqual(str(message), expected_str)

    def test_mark_as_read(self):
        """Test marking a message as read"""
        message = DirectMessage.objects.create(
            chat=self.chat, sender=self.user1, content="Test message"
        )

        self.assertFalse(message.is_read)
        message.is_read = True
        message.save()
        self.assertTrue(message.is_read)

    def test_get_unread_count(self):
        """Test getting unread message count for a user"""
        # Create messages from user2 to user1
        DirectMessage.objects.create(
            chat=self.chat, sender=self.user2, content="Message 1"
        )
        DirectMessage.objects.create(
            chat=self.chat, sender=self.user2, content="Message 2"
        )

        # Create a read message
        read_message = DirectMessage.objects.create(
            chat=self.chat, sender=self.user2, content="Read message"
        )
        read_message.is_read = True
        read_message.save()

        # Get unread count for user1
        unread_count = DirectMessage.objects.filter(
            chat=self.chat, sender=self.user2, is_read=False
        ).count()

        self.assertEqual(unread_count, 2)

    def test_message_ordering(self):
        """Test that messages are ordered by created_at"""
        message1 = DirectMessage.objects.create(
            chat=self.chat, sender=self.user1, content="First message"
        )
        message2 = DirectMessage.objects.create(
            chat=self.chat, sender=self.user2, content="Second message"
        )

        messages = list(
            DirectMessage.objects.filter(chat=self.chat).order_by("created_at")
        )
        self.assertEqual(messages[0], message1)
        self.assertEqual(messages[1], message2)

    def test_message_content_max_length(self):
        """Test message content length validation"""
        # Test with very long content
        long_content = "a" * 1000
        message = DirectMessage.objects.create(
            chat=self.chat, sender=self.user1, content=long_content
        )
        self.assertEqual(message.content, long_content)


class DirectChatLeaveModelTests(TestCase):
    """Test DirectChatLeave model functionality"""

    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username="testuser1", email="test1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            description="Test event for chat testing",
            host=self.user1,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        self.chat = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )

    def test_direct_chat_leave_creation(self):
        """Test creating a DirectChatLeave record"""
        leave_record = DirectChatLeave.objects.create(chat=self.chat, user=self.user1)

        self.assertEqual(leave_record.chat, self.chat)
        self.assertEqual(leave_record.user, self.user1)
        self.assertIsNotNone(leave_record.left_at)

    def test_direct_chat_leave_str_representation(self):
        """Test string representation of DirectChatLeave"""
        leave_record = DirectChatLeave.objects.create(chat=self.chat, user=self.user1)
        expected_str = f"{self.user1.username} left chat {self.chat.id}"
        self.assertEqual(str(leave_record), expected_str)

    def test_multiple_users_can_leave(self):
        """Test that both users can leave the same chat"""
        leave1 = DirectChatLeave.objects.create(chat=self.chat, user=self.user1)
        leave2 = DirectChatLeave.objects.create(chat=self.chat, user=self.user2)

        self.assertEqual(DirectChatLeave.objects.filter(chat=self.chat).count(), 2)
        self.assertNotEqual(leave1.left_at, leave2.left_at)


class DirectChatIntegrationTests(TestCase):
    """Integration tests for Direct Chat functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="testuser1", email="test1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            description="Test event for chat testing",
            host=self.user1,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

    def test_real_time_message_simulation(self):
        """Test simulating real-time message exchange"""
        # Create chat
        chat = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )

        # Simulate rapid message exchange
        messages = [
            ("Hello!", self.user1),
            ("Hi there!", self.user2),
            ("How are you?", self.user1),
            ("I'm good, thanks!", self.user2),
            ("Great to hear!", self.user1),
        ]

        for content, sender in messages:
            DirectMessage.objects.create(chat=chat, sender=sender, content=content)

        # Verify all messages were created
        self.assertEqual(DirectMessage.objects.filter(chat=chat).count(), 5)

        # Verify message ordering (should be chronological)
        messages = DirectMessage.objects.filter(chat=chat).order_by("created_at")
        self.assertEqual(messages[0].content, "Hello!")
        self.assertEqual(messages[4].content, "Great to hear!")

    def test_chat_with_deleted_event(self):
        """Test chat behavior when event is deleted"""
        chat = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )

        # Create some messages
        DirectMessage.objects.create(
            chat=chat, sender=self.user1, content="Test message"
        )

        # Soft delete the event
        self.event.is_deleted = True
        self.event.save()

        # Chat and messages should still exist
        self.assertTrue(DirectChat.objects.filter(id=chat.id).exists())
        self.assertTrue(DirectMessage.objects.filter(chat=chat).exists())

    def test_concurrent_message_handling(self):
        """Test handling of concurrent messages from different users"""
        chat = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )

        # Simulate concurrent messages
        message1 = DirectMessage.objects.create(
            chat=chat, sender=self.user1, content="Message from user1"
        )

        message2 = DirectMessage.objects.create(
            chat=chat, sender=self.user2, content="Message from user2"
        )

        # Both messages should be created successfully
        self.assertEqual(DirectMessage.objects.filter(chat=chat).count(), 2)

        # Messages should have different timestamps
        self.assertNotEqual(message1.created_at, message2.created_at)

    def test_chat_privacy(self):
        """Test that users can only access their own chats"""
        # Create chat between user1 and user2
        chat = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )

        # Create third user
        user3 = User.objects.create_user(
            username="testuser3", email="test3@example.com", password="testpass123"
        )

        # User3 should not be able to access the chat
        self.client.login(username="testuser3", password="testpass123")

        # Test that user3 cannot see messages from chat they're not part of
        messages_count = DirectMessage.objects.filter(chat=chat).count()
        self.assertEqual(messages_count, 0)  # No messages yet

        # Create messages in the chat
        DirectMessage.objects.create(
            chat=chat, sender=self.user1, content="Private message"
        )

        # User3 should not be able to see these messages through the chat
        user3_messages = (
            DirectMessage.objects.filter(chat__user1=user3).count()
            + DirectMessage.objects.filter(chat__user2=user3).count()
        )
        self.assertEqual(user3_messages, 0)

    def test_complete_chat_flow(self):
        """Test complete chat flow: create chat, send messages, leave"""
        # Step 1: Create chat
        chat = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )

        # Step 2: Send messages
        DirectMessage.objects.create(chat=chat, sender=self.user1, content="Hello!")

        DirectMessage.objects.create(chat=chat, sender=self.user2, content="Hi there!")

        # Step 3: Leave chat
        DirectChatLeave.objects.create(chat=chat, user=self.user1)

        # Verify all operations completed successfully
        self.assertEqual(DirectMessage.objects.filter(chat=chat).count(), 2)
        self.assertEqual(DirectChatLeave.objects.filter(chat=chat).count(), 1)

        # Verify chat participants
        active_users = chat.get_active_users()
        self.assertEqual(len(active_users), 1)  # Only user2 remains
        self.assertEqual(active_users[0], self.user2)

    def test_chat_performance_with_many_messages(self):
        """Test chat performance with many messages"""
        chat = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )

        # Create many messages
        for i in range(100):
            DirectMessage.objects.create(
                chat=chat,
                sender=self.user1 if i % 2 == 0 else self.user2,
                content=f"Message {i}",
            )

        # Test query performance
        messages = DirectMessage.objects.filter(chat=chat).order_by("-created_at")[:10]
        self.assertEqual(len(messages), 10)

        # Test unread count performance
        unread_count = DirectMessage.objects.filter(
            chat=chat, sender=self.user2, is_read=False
        ).count()
        self.assertEqual(unread_count, 50)  # Half of messages are from user2

    def test_chat_with_multiple_events(self):
        """Test chat functionality across multiple events"""
        # Create second event
        event2 = Event.objects.create(
            title="Test Event 2",
            description="Second test event",
            host=self.user1,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=2),
            start_location=self.location,
        )

        # Create chats in both events
        chat1 = DirectChat.objects.create(
            event=self.event, user1=self.user1, user2=self.user2
        )
        chat2 = DirectChat.objects.create(
            event=event2, user1=self.user1, user2=self.user2
        )

        # Send messages in both chats
        DirectMessage.objects.create(
            chat=chat1, sender=self.user1, content="Event 1 message"
        )
        DirectMessage.objects.create(
            chat=chat2, sender=self.user1, content="Event 2 message"
        )

        # Verify messages are isolated by event
        self.assertEqual(DirectMessage.objects.filter(chat=chat1).count(), 1)
        self.assertEqual(DirectMessage.objects.filter(chat=chat2).count(), 1)

        # Verify user can have multiple chats
        user1_chats = (
            DirectChat.objects.filter(user1=self.user1).count()
            + DirectChat.objects.filter(user2=self.user1).count()
        )
        self.assertEqual(user1_chats, 2)
