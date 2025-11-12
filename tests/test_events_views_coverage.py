"""
Comprehensive test coverage for events/views.py
Targets uncovered lines to boost coverage from 51% to 90%+
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from loc_detail.models import PublicArt
from events.models import (
    Event,
    EventLocation,
    EventInvite,
    EventJoinRequest,
    EventChatMessage,
    DirectChat,
    DirectChatLeave,
    EventMembership,
)
from events.enums import MembershipRole
from events.enums import (
    EventVisibility,
    InviteStatus,
    MessageReportReason,
)
import json


class CreateEventViewTests(TestCase):
    """Test event creation with edge cases and validation errors"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testhost", password="testpass")
        self.client.login(username="testhost", password="testpass")
        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

    def test_create_event_with_invalid_form(self):
        """Test event creation with invalid form data (line 51-59)"""
        response = self.client.post(
            reverse("events:create"),
            {
                "title": "",  # Empty title should fail validation
                "description": "Test Description",
                "start_time": (timezone.now() + timedelta(days=1)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "visibility": EventVisibility.PUBLIC_OPEN,
            },
        )

        # Should stay on create page with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/create.html")


class DetailViewTests(TestCase):
    """Test event detail view with various user roles"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username="host", password="testpass")
        self.attendee = User.objects.create_user(
            username="attendee", password="testpass"
        )
        self.visitor = User.objects.create_user(username="visitor", password="testpass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            host=self.host,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_INVITE,
        )
        EventMembership.objects.create(
            event=self.event, user=self.attendee, role=MembershipRole.ATTENDEE
        )

    def test_detail_event_not_found(self):
        """Test detail view with non-existent event (line 186-187)"""
        self.client.login(username="host", password="testpass")
        response = self.client.get(
            reverse("events:detail", kwargs={"slug": "nonexistent"})
        )

        # Should redirect to public events with error message
        self.assertRedirects(response, reverse("events:public"))

    def test_detail_view_as_host(self):
        """Test detail view shows join requests for host (line 193)"""
        self.client.login(username="host", password="testpass")

        # Create a join request
        EventJoinRequest.objects.create(
            event=self.event,
            requester=self.visitor,
        )

        response = self.client.get(
            reverse("events:detail", kwargs={"slug": self.event.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("join_requests", response.context)
        self.assertEqual(len(response.context["join_requests"]), 1)

    def test_detail_view_as_visitor_with_join_request(self):
        """Test detail view shows join request status for visitor (line 201-203)"""
        self.client.login(username="visitor", password="testpass")

        # Create a join request
        join_request = EventJoinRequest.objects.create(
            event=self.event,
            requester=self.visitor,
        )

        response = self.client.get(
            reverse("events:detail", kwargs={"slug": self.event.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("join_request", response.context)
        self.assertEqual(response.context["join_request"], join_request)


class JoinEventViewTests(TestCase):
    """Test join event functionality with error handling"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username="host", password="testpass")
        self.user = User.objects.create_user(username="user", password="testpass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            host=self.host,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )

    def test_join_event_with_error(self):
        """Test join event with service error (line 210-223)"""
        self.client.login(username="user", password="testpass")

        # Join event first time
        self.client.post(reverse("events:join", kwargs={"slug": self.event.slug}))

        # Try to join again (should fail)
        response = self.client.post(
            reverse("events:join", kwargs={"slug": self.event.slug})
        )

        # Should redirect back to public events
        self.assertRedirects(response, reverse("events:public"))

    def test_join_event_preserves_query_params(self):
        """Test join event redirects with query params (line 218-220)"""
        self.client.login(username="user", password="testpass")

        # Join with query params
        response = self.client.post(
            reverse("events:join", kwargs={"slug": self.event.slug})
            + "?q=test&filter=open"
        )

        # Should preserve query params in redirect
        self.assertRedirects(response, reverse("events:public") + "?q=test&filter=open")


class InvitationViewTests(TestCase):
    """Test invitation accept/decline with edge cases"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username="host", password="testpass")
        self.invitee = User.objects.create_user(username="invitee", password="testpass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            host=self.host,
            start_location=self.location,
            visibility=EventVisibility.PRIVATE,
        )

        self.invite = EventInvite.objects.create(
            event=self.event,
            invitee=self.invitee,
            status=InviteStatus.PENDING,
        )

    def test_accept_invite_with_exception(self):
        """Test accept invite handling exceptions (line 230-241)"""
        self.client.login(username="invitee", password="testpass")

        # Delete event to trigger exception
        self.event.is_deleted = True
        self.event.save()

        response = self.client.post(
            reverse("events:accept", kwargs={"slug": self.event.slug})
        )

        # Should handle error gracefully
        self.assertEqual(response.status_code, 302)


class APIViewTests(TestCase):
    """Test API endpoints with edge cases"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

    def test_api_locations_search_short_term(self):
        """Test location search with term < 2 chars (line 275)"""
        response = self.client.get(reverse("events:api_locations_search"), {"q": "a"})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["results"], [])

    def test_api_users_search_short_term(self):
        """Test user search with term < 2 chars (line 306-330)"""
        response = self.client.get(reverse("events:api_users_search"), {"q": "u"})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["results"], [])

    def test_api_chat_messages_non_member(self):
        """Test chat messages API for non-member (line 340-351)"""
        host = User.objects.create_user(username="host", password="testpass")
        location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )
        event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            host=host,
            start_location=location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )

        # User is not a member, should get 403
        response = self.client.get(
            reverse("events:api_chat_messages", kwargs={"slug": event.slug})
        )

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertIn("error", data)


class ChatSendViewTests(TestCase):
    """Test chat message sending with errors"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username="host", password="testpass")
        self.attendee = User.objects.create_user(
            username="attendee", password="testpass"
        )

        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            host=self.host,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )
        EventMembership.objects.create(
            event=self.event, user=self.attendee, role=MembershipRole.ATTENDEE
        )

    def test_chat_send_with_error(self):
        """Test chat send with service error (line 358-368)"""
        self.client.login(username="attendee", password="testpass")

        # Try to send empty message (should fail)
        response = self.client.post(
            reverse("events:chat_send", kwargs={"slug": self.event.slug}),
            {"message": ""},
        )

        # Should redirect back with error
        self.assertRedirects(response, self.event.get_absolute_url() + "#chat")


class JoinRequestViewTests(TestCase):
    """Test join request functionality"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username="host", password="testpass")
        self.user = User.objects.create_user(username="user", password="testpass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            host=self.host,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_INVITE,
        )

    def test_request_join_with_error(self):
        """Test request join with error (line 375-395)"""
        self.client.login(username="user", password="testpass")

        # Create duplicate request
        EventJoinRequest.objects.create(event=self.event, requester=self.user)

        # Try again (should fail)
        response = self.client.post(
            reverse("events:request_join", kwargs={"slug": self.event.slug})
        )

        # Should redirect back to event detail
        self.assertRedirects(response, self.event.get_absolute_url())

    def test_approve_request_non_host(self):
        """Test approve request by non-host (line 402-420)"""
        self.client.login(username="user", password="testpass")

        join_request = EventJoinRequest.objects.create(
            event=self.event, requester=self.user
        )

        # Try to approve as non-host
        User.objects.create_user(username="other", password="testpass")
        self.client.login(username="other", password="testpass")

        response = self.client.post(
            reverse(
                "events:approve_request",
                kwargs={"slug": self.event.slug, "request_id": join_request.id},
            )
        )

        # Should redirect with error
        self.assertRedirects(response, self.event.get_absolute_url())

    def test_approve_request_with_exception(self):
        """Test approve request with exception (line 436-455)"""
        self.client.login(username="host", password="testpass")

        join_request = EventJoinRequest.objects.create(
            event=self.event, requester=self.user
        )

        # Corrupt data to trigger exception
        join_request.status = "APPROVED"
        join_request.save()

        response = self.client.post(
            reverse(
                "events:approve_request",
                kwargs={"slug": self.event.slug, "request_id": join_request.id},
            )
        )

        # Should handle error
        self.assertRedirects(response, self.event.get_absolute_url())

    def test_decline_request_non_host(self):
        """Test decline request by non-host"""
        join_request = EventJoinRequest.objects.create(
            event=self.event, requester=self.user
        )

        # Try to decline as non-host
        User.objects.create_user(username="other", password="testpass")
        self.client.login(username="other", password="testpass")

        response = self.client.post(
            reverse(
                "events:decline_request",
                kwargs={"slug": self.event.slug, "request_id": join_request.id},
            )
        )

        # Should redirect with error
        self.assertRedirects(response, self.event.get_absolute_url())


class UpdateEventViewTests(TestCase):
    """Test event update functionality"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username="host", password="testpass")
        self.user = User.objects.create_user(username="user", password="testpass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            host=self.host,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )

    def test_update_event_non_host(self):
        """Test update event by non-host (line 496-498)"""
        self.client.login(username="user", password="testpass")

        response = self.client.get(
            reverse("events:update", kwargs={"slug": self.event.slug})
        )

        # Should redirect with error
        self.assertRedirects(response, self.event.get_absolute_url())

    def test_update_event_get_with_locations(self):
        """Test update event GET request with existing locations (line 529-530)"""
        self.client.login(username="host", password="testpass")

        # Add location to event
        EventLocation.objects.create(
            event=self.event,
            location=self.location,
            order=1,
        )

        response = self.client.get(
            reverse("events:update", kwargs={"slug": self.event.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("existing_locations", response.context)
        self.assertEqual(len(response.context["existing_locations"]), 1)

    def test_update_event_post_with_error(self):
        """Test update event POST with validation error (line 547-548)"""
        self.client.login(username="host", password="testpass")

        response = self.client.post(
            reverse("events:update", kwargs={"slug": self.event.slug}),
            {
                "title": "",  # Empty title
                "description": "Updated Description",
                "start_time": (timezone.now() + timedelta(days=1)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "visibility": EventVisibility.PUBLIC_OPEN,
            },
        )

        # Should stay on update page
        self.assertEqual(response.status_code, 200)


class DeleteEventViewTests(TestCase):
    """Test event deletion"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username="host", password="testpass")
        self.user = User.objects.create_user(username="user", password="testpass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            host=self.host,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )

    def test_delete_event_non_host(self):
        """Test delete event by non-host (line 557-582)"""
        self.client.login(username="user", password="testpass")

        response = self.client.post(
            reverse("events:delete", kwargs={"slug": self.event.slug})
        )

        # Should redirect with error
        self.assertRedirects(response, self.event.get_absolute_url())


class LeaveEventViewTests(TestCase):
    """Test leave event functionality"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username="host", password="testpass")
        self.attendee = User.objects.create_user(
            username="attendee", password="testpass"
        )

        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            host=self.host,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )
        EventMembership.objects.create(
            event=self.event, user=self.attendee, role=MembershipRole.ATTENDEE
        )

    def test_leave_event_with_error(self):
        """Test leave event with service error (line 589-620)"""
        self.client.login(username="attendee", password="testpass")

        # Leave event first time
        self.client.post(reverse("events:leave", kwargs={"slug": self.event.slug}))

        # Try again (should fail)
        response = self.client.post(
            reverse("events:leave", kwargs={"slug": self.event.slug})
        )

        # Should redirect back to event
        self.assertRedirects(response, self.event.get_absolute_url())


class FavoriteEventViewTests(TestCase):
    """Test favorite/unfavorite functionality"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username="host", password="testpass")
        self.user = User.objects.create_user(username="user", password="testpass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            host=self.host,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )

    def test_favorite_event_with_error(self):
        """Test favorite event with error (line 627-657)"""
        self.client.login(username="user", password="testpass")

        # Favorite twice (second should fail)
        self.client.post(reverse("events:favorite", kwargs={"slug": self.event.slug}))
        response = self.client.post(
            reverse("events:favorite", kwargs={"slug": self.event.slug})
        )

        # Should redirect back
        self.assertEqual(response.status_code, 302)

    def test_unfavorite_event_with_error(self):
        """Test unfavorite event with exception (line 664-692)"""
        self.client.login(username="user", password="testpass")

        # Try to unfavorite without favoriting first
        response = self.client.post(
            reverse("events:unfavorite", kwargs={"slug": self.event.slug})
        )

        # Should handle error
        self.assertEqual(response.status_code, 302)


class ReportMessageViewTests(TestCase):
    """Test message reporting functionality"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username="host", password="testpass")
        self.user = User.objects.create_user(username="user", password="testpass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            host=self.host,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )

        self.message = EventChatMessage.objects.create(
            event=self.event,
            author=self.host,
            message="Test message",
        )

    def test_report_message_invalid_reason(self):
        """Test report message with invalid reason (line 698-722)"""
        self.client.login(username="user", password="testpass")

        response = self.client.post(
            reverse("events:report_message", kwargs={"message_id": self.message.id}),
            {"reason": "INVALID", "description": "Test"},
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_report_message_duplicate(self):
        """Test reporting same message twice (line 730-770)"""
        self.client.login(username="user", password="testpass")

        # Report once
        self.client.post(
            reverse("events:report_message", kwargs={"message_id": self.message.id}),
            {"reason": MessageReportReason.SPAM, "description": "Test"},
        )

        # Try again
        response = self.client.post(
            reverse("events:report_message", kwargs={"message_id": self.message.id}),
            {"reason": MessageReportReason.SPAM, "description": "Test"},
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("already reported", data["error"])


class DirectChatViewTests(TestCase):
    """Test direct chat functionality"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username="host", password="testpass")
        self.user1 = User.objects.create_user(username="user1", password="testpass")
        self.user2 = User.objects.create_user(username="user2", password="testpass")
        self.visitor = User.objects.create_user(username="visitor", password="testpass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            host=self.host,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )
        EventMembership.objects.create(
            event=self.event, user=self.user1, role=MembershipRole.ATTENDEE
        )
        EventMembership.objects.create(
            event=self.event, user=self.user2, role=MembershipRole.ATTENDEE
        )

    def test_create_direct_chat_user_not_found(self):
        """Test create direct chat with non-existent user (line 776-797)"""
        self.client.login(username="user1", password="testpass")

        response = self.client.post(
            reverse("events:create_direct_chat", kwargs={"slug": self.event.slug}),
            {"other_user_id": 999999},
        )

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_create_direct_chat_non_member(self):
        """Test create direct chat with non-member"""
        self.client.login(username="user1", password="testpass")

        response = self.client.post(
            reverse("events:create_direct_chat", kwargs={"slug": self.event.slug}),
            {"other_user_id": self.visitor.id},
        )

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_send_direct_message_unauthorized(self):
        """Test send direct message by unauthorized user"""
        chat = DirectChat.objects.create(
            event=self.event,
            user1=self.user1,
            user2=self.user2,
        )

        # Try as visitor
        self.client.login(username="visitor", password="testpass")

        response = self.client.post(
            reverse("events:send_direct_message", kwargs={"chat_id": chat.id}),
            {"content": "Test message"},
        )

        self.assertEqual(response.status_code, 403)

    def test_send_direct_message_empty(self):
        """Test send empty direct message"""
        chat = DirectChat.objects.create(
            event=self.event,
            user1=self.user1,
            user2=self.user2,
        )

        self.client.login(username="user1", password="testpass")

        response = self.client.post(
            reverse("events:send_direct_message", kwargs={"chat_id": chat.id}),
            {"content": ""},
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_send_direct_message_too_long(self):
        """Test send too long direct message"""
        chat = DirectChat.objects.create(
            event=self.event,
            user1=self.user1,
            user2=self.user2,
        )

        self.client.login(username="user1", password="testpass")

        response = self.client.post(
            reverse("events:send_direct_message", kwargs={"chat_id": chat.id}),
            {"content": "x" * 501},  # Exceeds 500 char limit
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_send_direct_message_restores_left_chat(self):
        """Test sending message restores chat for user who left"""
        chat = DirectChat.objects.create(
            event=self.event,
            user1=self.user1,
            user2=self.user2,
        )

        # User2 leaves
        DirectChatLeave.objects.create(chat=chat, user=self.user2)

        # User1 sends message
        self.client.login(username="user1", password="testpass")

        response = self.client.post(
            reverse("events:send_direct_message", kwargs={"chat_id": chat.id}),
            {"content": "Hello again"},
        )

        self.assertEqual(response.status_code, 200)
        # User2 should be restored (leave record deleted)
        self.assertFalse(
            DirectChatLeave.objects.filter(chat=chat, user=self.user2).exists()
        )

    def test_api_direct_messages_unauthorized(self):
        """Test get direct messages by unauthorized user"""
        chat = DirectChat.objects.create(
            event=self.event,
            user1=self.user1,
            user2=self.user2,
        )

        self.client.login(username="visitor", password="testpass")

        response = self.client.get(
            reverse("events:api_direct_messages", kwargs={"chat_id": chat.id})
        )

        self.assertEqual(response.status_code, 403)

    def test_delete_direct_chat_already_left(self):
        """Test deleting chat that user already left"""
        chat = DirectChat.objects.create(
            event=self.event,
            user1=self.user1,
            user2=self.user2,
        )

        # User leaves
        DirectChatLeave.objects.create(chat=chat, user=self.user1)

        self.client.login(username="user1", password="testpass")

        response = self.client.post(
            reverse("events:delete_direct_chat", kwargs={"chat_id": chat.id})
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("already left", data["error"])

    def test_delete_direct_chat_not_found(self):
        """Test deleting non-existent chat"""
        self.client.login(username="user1", password="testpass")

        response = self.client.post(
            reverse("events:delete_direct_chat", kwargs={"chat_id": 999999})
        )

        self.assertEqual(response.status_code, 404)


class ChatSendMessageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
            latitude=40.7128,
            longitude=-74.0060,
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.user,
            start_time=timezone.now() + timedelta(hours=2),
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )
        # Make user a member
        EventMembership.objects.create(
            event=self.event, user=self.user, role=MembershipRole.HOST
        )

    def test_send_chat_message_as_member(self):
        """Test sending a chat message as event member"""
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("events:chat_send", args=[self.event.slug]),
            {"message": "Hello everyone!"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

    def test_send_empty_chat_message(self):
        """Test sending empty chat message"""
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("events:chat_send", args=[self.event.slug]),
            {"message": ""},
            follow=True,
        )

        # Should handle gracefully
        self.assertEqual(response.status_code, 200)


class APIChatMessagesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.visitor = User.objects.create_user(
            username="visitor", email="visitor@example.com", password="password123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
            latitude=40.7128,
            longitude=-74.0060,
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.user,
            start_time=timezone.now() + timedelta(hours=2),
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )
        EventMembership.objects.create(
            event=self.event, user=self.user, role=MembershipRole.HOST
        )

    def test_api_chat_messages_as_member(self):
        """Test API chat messages endpoint for members"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(
            reverse("events:api_chat_messages", args=[self.event.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_api_chat_messages_as_visitor_forbidden(self):
        """Test API chat messages forbidden for non-members"""
        self.client.login(username="visitor", password="password123")
        response = self.client.get(
            reverse("events:api_chat_messages", args=[self.event.slug])
        )

        # Should be forbidden
        self.assertEqual(response.status_code, 403)


class JoinRequestFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(
            username="host", email="host@example.com", password="password123"
        )
        self.requester = User.objects.create_user(
            username="requester", email="requester@example.com", password="password123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
            latitude=40.7128,
            longitude=-74.0060,
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.host,
            start_time=timezone.now() + timedelta(hours=2),
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_INVITE,
        )

    def test_request_join_creates_request(self):
        """Test requesting to join event creates join request"""
        self.client.login(username="requester", password="password123")
        response = self.client.post(
            reverse("events:request_join", args=[self.event.slug]), follow=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            EventJoinRequest.objects.filter(
                event=self.event, requester=self.requester
            ).exists()
        )

    def test_cannot_request_join_twice(self):
        """Test cannot create duplicate join requests"""
        # Create first request
        EventJoinRequest.objects.create(event=self.event, requester=self.requester)

        self.client.login(username="requester", password="password123")
        response = self.client.post(
            reverse("events:request_join", args=[self.event.slug]), follow=True
        )

        # Should handle gracefully
        self.assertEqual(response.status_code, 200)


class EventDetailContextTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
            latitude=40.7128,
            longitude=-74.0060,
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.user,
            start_time=timezone.now() + timedelta(hours=2),
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )

    def test_event_detail_shows_host_badge(self):
        """Test event detail page shows host badge for creator"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("events:detail", args=[self.event.slug]))

        self.assertEqual(response.status_code, 200)
        # Should show that user is host
        self.assertContains(response, "You are the host")

    def test_event_detail_requires_login(self):
        """Test event detail page requires login"""
        response = self.client.get(reverse("events:detail", args=[self.event.slug]))

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login", response.url)


class EventIndexViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

    def test_events_index_redirects_to_public(self):
        """Test events index redirects to public events page"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("events:index"))

        # Should redirect to public events
        self.assertEqual(response.status_code, 302)
        self.assertIn("/events/public", response.url)

    def test_events_index_accessible_when_authenticated(self):
        """Test events index redirects for authenticated users"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("events:index"), follow=True)

        # Should follow redirect to public events and succeed
        self.assertEqual(response.status_code, 200)


class CreateEventFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

    def test_create_event_get_request(self):
        """Test GET request to create event page"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("events:create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Event")

    def test_create_event_with_invalid_datetime(self):
        """Test creating event with past datetime"""
        self.client.login(username="testuser", password="password123")
        past_time = timezone.now() - timedelta(hours=1)

        response = self.client.post(
            reverse("events:create"),
            {
                "title": "Past Event",
                "description": "This is in the past",
                "event_type": "PUBLIC_OPEN",
                "datetime": past_time.strftime("%Y-%m-%dT%H:%M"),
            },
        )

        # Should stay on create page with errors
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Event.objects.filter(title="Past Event").exists())


class UpdateEventFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
            latitude=40.7128,
            longitude=-74.0060,
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.user,
            start_time=timezone.now() + timedelta(hours=2),
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )

    def test_update_event_get_request(self):
        """Test GET request to update event page"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("events:update", args=[self.event.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event")
