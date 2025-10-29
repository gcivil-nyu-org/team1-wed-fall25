"""
Comprehensive test suite for Events app
Tests models, services, selectors, views, and forms
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from events.models import (
    Event,
    EventMembership,
    EventLocation,
    EventInvite,
    EventChatMessage,
    EventJoinRequest,
    EventFavorite,
)
from events.enums import (
    EventVisibility,
    MembershipRole,
    InviteStatus,
    JoinRequestStatus,
)
from events.services import (
    create_event,
    join_event,
    accept_invite,
    decline_invite,
    post_chat_message,
    request_join,
    approve_join_request,
    decline_join_request,
    update_event,
    delete_event,
    leave_event,
    favorite_event,
    unfavorite_event,
)
from loc_detail.models import PublicArt


class EventModelTests(TestCase):
    """Test Event model functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art", latitude=40.7128, longitude=-74.0060
        )

    def test_event_creation(self):
        """Test basic event creation"""
        event = Event.objects.create(
            title="Test Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
            description="Test Description",
        )
        self.assertIsNotNone(event.slug)
        self.assertFalse(event.is_deleted)
        self.assertEqual(str(event), f"Test Event by {self.user.username}")

    def test_slug_generation(self):
        """Test that slug is auto-generated"""
        event = Event.objects.create(
            title="My Amazing Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        self.assertTrue(event.slug.startswith("my-amazing-event"))
        self.assertIn("-", event.slug)

    def test_get_absolute_url(self):
        """Test get_absolute_url returns correct URL"""
        event = Event.objects.create(
            title="URL Test",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        expected_url = reverse("events:detail", kwargs={"slug": event.slug})
        self.assertEqual(event.get_absolute_url(), expected_url)

    def test_event_ordering(self):
        """Test events are ordered by start_time descending"""
        event1 = Event.objects.create(
            title="Event 1",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        event2 = Event.objects.create(
            title="Event 2",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=2),
            start_location=self.location,
        )
        events = list(Event.objects.all())
        self.assertEqual(events[0], event2)  # Later event comes first
        self.assertEqual(events[1], event1)


class EventLocationModelTests(TestCase):
    """Test EventLocation model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.location1 = PublicArt.objects.create(
            title="Art 1", latitude=40.7128, longitude=-74.0060
        )
        self.location2 = PublicArt.objects.create(
            title="Art 2", latitude=40.7589, longitude=-73.9851
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location1,
        )

    def test_event_location_creation(self):
        """Test creating event locations"""
        loc = EventLocation.objects.create(
            event=self.event, location=self.location2, order=1
        )
        self.assertEqual(str(loc), f"{self.event.title} - Stop 1")

    def test_location_ordering(self):
        """Test locations are ordered by order field"""
        loc2 = EventLocation.objects.create(
            event=self.event, location=self.location2, order=2
        )
        loc1 = EventLocation.objects.create(
            event=self.event, location=self.location1, order=1
        )
        locations = list(EventLocation.objects.filter(event=self.event))
        self.assertEqual(locations[0], loc1)
        self.assertEqual(locations[1], loc2)


class EventMembershipModelTests(TestCase):
    """Test EventMembership model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

    def test_membership_creation(self):
        """Test creating membership"""
        membership = EventMembership.objects.create(
            event=self.event, user=self.user, role=MembershipRole.HOST
        )
        self.assertEqual(
            str(membership), f"{self.user.username} - HOST at {self.event.title}"
        )

    def test_unique_event_user_constraint(self):
        """Test that a user can't have duplicate memberships"""
        EventMembership.objects.create(
            event=self.event, user=self.user, role=MembershipRole.HOST
        )
        with self.assertRaises(Exception):  # IntegrityError
            EventMembership.objects.create(
                event=self.event, user=self.user, role=MembershipRole.ATTENDEE
            )


class EventInviteModelTests(TestCase):
    """Test EventInvite model"""

    def setUp(self):
        self.host = User.objects.create_user(
            username="host", email="host@test.com", password="testpass123"
        )
        self.invitee = User.objects.create_user(
            username="invitee", email="invitee@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.host,
            visibility=EventVisibility.PUBLIC_INVITE,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

    def test_invite_creation(self):
        """Test creating an invite"""
        invite = EventInvite.objects.create(
            event=self.event,
            invited_by=self.host,
            invitee=self.invitee,
            status=InviteStatus.PENDING,
        )
        self.assertEqual(
            str(invite), f"Invite to {self.invitee.username} for {self.event.title}"
        )
        self.assertEqual(invite.status, InviteStatus.PENDING)
        self.assertIsNone(invite.responded_at)


class EventChatMessageModelTests(TestCase):
    """Test EventChatMessage model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

    def test_chat_message_creation(self):
        """Test creating a chat message"""
        msg = EventChatMessage.objects.create(
            event=self.event, author=self.user, message="Hello everyone!"
        )
        self.assertEqual(str(msg), f"{self.user.username}: Hello everyone!")

    def test_chat_message_ordering(self):
        """Test messages are ordered by created_at"""
        import time

        EventChatMessage.objects.create(
            event=self.event, author=self.user, message="First"
        )
        time.sleep(0.01)  # Ensure different timestamps
        EventChatMessage.objects.create(
            event=self.event, author=self.user, message="Second"
        )
        messages = list(EventChatMessage.objects.filter(event=self.event))
        self.assertEqual(messages[0].message, "First")
        self.assertEqual(messages[1].message, "Second")


class EventJoinRequestModelTests(TestCase):
    """Test EventJoinRequest model"""

    def setUp(self):
        self.host = User.objects.create_user(
            username="host", email="host@test.com", password="testpass123"
        )
        self.requester = User.objects.create_user(
            username="requester", email="requester@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.host,
            visibility=EventVisibility.PUBLIC_INVITE,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

    def test_join_request_creation(self):
        """Test creating a join request"""
        request = EventJoinRequest.objects.create(
            event=self.event,
            requester=self.requester,
            status=JoinRequestStatus.PENDING,
        )
        self.assertEqual(
            str(request),
            f"Join request by {self.requester.username} for {self.event.title}",
        )
        self.assertEqual(request.status, JoinRequestStatus.PENDING)


class EventFavoriteModelTests(TestCase):
    """Test EventFavorite model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

    def test_favorite_creation(self):
        """Test creating a favorite"""
        fav = EventFavorite.objects.create(event=self.event, user=self.user)
        self.assertEqual(str(fav), f"{self.user.username} favorited {self.event.title}")

    def test_unique_event_user_favorite(self):
        """Test that a user can't favorite the same event twice"""
        EventFavorite.objects.create(event=self.event, user=self.user)
        with self.assertRaises(Exception):  # IntegrityError
            EventFavorite.objects.create(event=self.event, user=self.user)


class CreateEventServiceTests(TestCase):
    """Test create_event service"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.invitee = User.objects.create_user(
            username="invitee", email="invitee@test.com", password="testpass123"
        )
        self.location1 = PublicArt.objects.create(
            title="Art 1", latitude=40.7128, longitude=-74.0060
        )
        self.location2 = PublicArt.objects.create(
            title="Art 2", latitude=40.7589, longitude=-73.9851
        )

    def test_create_basic_event(self):
        """Test creating a basic event"""
        from events.forms import EventForm

        form_data = {
            "title": "Test Event",
            "start_time": timezone.now() + timedelta(days=1),
            "start_location": self.location1,
            "visibility": EventVisibility.PUBLIC_OPEN,
            "description": "Test description",
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

        event = create_event(host=self.user, form=form, locations=[], invites=[])

        self.assertEqual(event.title, "Test Event")
        self.assertEqual(event.host, self.user)
        self.assertTrue(
            EventMembership.objects.filter(
                event=event, user=self.user, role=MembershipRole.HOST
            ).exists()
        )

    def test_create_event_with_locations(self):
        """Test creating event with additional locations"""
        from events.forms import EventForm

        form_data = {
            "title": "Multi-Stop Event",
            "start_time": timezone.now() + timedelta(days=1),
            "start_location": self.location1,
            "visibility": EventVisibility.PUBLIC_OPEN,
            "description": "",
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

        event = create_event(
            host=self.user, form=form, locations=[self.location2.id], invites=[]
        )

        self.assertEqual(EventLocation.objects.filter(event=event).count(), 1)
        loc = EventLocation.objects.get(event=event)
        self.assertEqual(loc.location, self.location2)
        self.assertEqual(loc.order, 1)

    def test_create_event_with_invites(self):
        """Test creating event with invites"""
        from events.forms import EventForm

        form_data = {
            "title": "Invite Event",
            "start_time": timezone.now() + timedelta(days=1),
            "start_location": self.location1,
            "visibility": EventVisibility.PUBLIC_INVITE,
            "description": "",
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

        event = create_event(
            host=self.user, form=form, locations=[], invites=[self.invitee.id]
        )

        self.assertTrue(
            EventInvite.objects.filter(
                event=event, invitee=self.invitee, status=InviteStatus.PENDING
            ).exists()
        )
        self.assertTrue(
            EventMembership.objects.filter(
                event=event, user=self.invitee, role=MembershipRole.INVITED
            ).exists()
        )

    def test_create_event_deduplicates_locations(self):
        """Test that duplicate locations are removed"""
        from events.forms import EventForm

        form_data = {
            "title": "Dedup Test",
            "start_time": timezone.now() + timedelta(days=1),
            "start_location": self.location1,
            "visibility": EventVisibility.PUBLIC_OPEN,
            "description": "",
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Pass duplicate location IDs
        event = create_event(
            host=self.user,
            form=form,
            locations=[self.location2.id, self.location2.id],
            invites=[],
        )

        # Should only have one location
        self.assertEqual(EventLocation.objects.filter(event=event).count(), 1)

    def test_create_event_excludes_host_from_invites(self):
        """Test that host is not added to invites"""
        from events.forms import EventForm

        form_data = {
            "title": "Host Invite Test",
            "start_time": timezone.now() + timedelta(days=1),
            "start_location": self.location1,
            "visibility": EventVisibility.PUBLIC_OPEN,
            "description": "",
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Try to invite the host (should be filtered out)
        event = create_event(
            host=self.user, form=form, locations=[], invites=[self.user.id]
        )

        # No invites should be created
        self.assertEqual(EventInvite.objects.filter(event=event).count(), 0)


class JoinEventServiceTests(TestCase):
    """Test join_event service"""

    def setUp(self):
        self.host = User.objects.create_user(
            username="host", email="host@test.com", password="testpass123"
        )
        self.visitor = User.objects.create_user(
            username="visitor", email="visitor@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )

    def test_join_public_open_event(self):
        """Test joining a PUBLIC_OPEN event"""
        event = Event.objects.create(
            title="Open Event",
            host=self.host,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

        join_event(event=event, user=self.visitor)

        self.assertTrue(
            EventMembership.objects.filter(
                event=event, user=self.visitor, role=MembershipRole.ATTENDEE
            ).exists()
        )

    def test_cannot_join_private_event(self):
        """Test that private events cannot be joined"""
        event = Event.objects.create(
            title="Private Event",
            host=self.host,
            visibility=EventVisibility.PRIVATE,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

        with self.assertRaises(ValueError) as context:
            join_event(event=event, user=self.visitor)

        self.assertIn("private", str(context.exception).lower())

    def test_join_invite_only_with_invite(self):
        """Test joining PUBLIC_INVITE event with valid invite"""
        event = Event.objects.create(
            title="Invite Event",
            host=self.host,
            visibility=EventVisibility.PUBLIC_INVITE,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        EventInvite.objects.create(
            event=event,
            invited_by=self.host,
            invitee=self.visitor,
            status=InviteStatus.PENDING,
        )

        join_event(event=event, user=self.visitor)

        self.assertTrue(
            EventMembership.objects.filter(
                event=event, user=self.visitor, role=MembershipRole.ATTENDEE
            ).exists()
        )

    def test_cannot_join_invite_only_without_invite(self):
        """Test cannot join PUBLIC_INVITE without invite"""
        event = Event.objects.create(
            title="Invite Event",
            host=self.host,
            visibility=EventVisibility.PUBLIC_INVITE,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

        with self.assertRaises(ValueError) as context:
            join_event(event=event, user=self.visitor)

        self.assertIn("invited", str(context.exception).lower())

    def test_cannot_join_twice(self):
        """Test that user cannot join the same event twice"""
        event = Event.objects.create(
            title="Open Event",
            host=self.host,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

        join_event(event=event, user=self.visitor)

        with self.assertRaises(ValueError) as context:
            join_event(event=event, user=self.visitor)

        self.assertIn("already joined", str(context.exception).lower())


class InviteServiceTests(TestCase):
    """Test accept_invite and decline_invite services"""

    def setUp(self):
        self.host = User.objects.create_user(
            username="host", email="host@test.com", password="testpass123"
        )
        self.invitee = User.objects.create_user(
            username="invitee", email="invitee@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.host,
            visibility=EventVisibility.PUBLIC_INVITE,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        self.invite = EventInvite.objects.create(
            event=self.event,
            invited_by=self.host,
            invitee=self.invitee,
            status=InviteStatus.PENDING,
        )
        EventMembership.objects.create(
            event=self.event, user=self.invitee, role=MembershipRole.INVITED
        )

    def test_accept_invite(self):
        """Test accepting an invite"""
        accept_invite(invite=self.invite)

        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, InviteStatus.ACCEPTED)
        self.assertIsNotNone(self.invite.responded_at)

        # Membership should be updated to ATTENDEE
        membership = EventMembership.objects.get(event=self.event, user=self.invitee)
        self.assertEqual(membership.role, MembershipRole.ATTENDEE)

    def test_decline_invite(self):
        """Test declining an invite"""
        decline_invite(invite=self.invite)

        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, InviteStatus.DECLINED)
        self.assertIsNotNone(self.invite.responded_at)

        # INVITED membership should be removed
        self.assertFalse(
            EventMembership.objects.filter(
                event=self.event, user=self.invitee, role=MembershipRole.INVITED
            ).exists()
        )


class ChatServiceTests(TestCase):
    """Test post_chat_message service"""

    def setUp(self):
        self.host = User.objects.create_user(
            username="host", email="host@test.com", password="testpass123"
        )
        self.attendee = User.objects.create_user(
            username="attendee", email="attendee@test.com", password="testpass123"
        )
        self.visitor = User.objects.create_user(
            username="visitor", email="visitor@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.host,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        EventMembership.objects.create(
            event=self.event, user=self.host, role=MembershipRole.HOST
        )
        EventMembership.objects.create(
            event=self.event, user=self.attendee, role=MembershipRole.ATTENDEE
        )

    def test_member_can_post_message(self):
        """Test that event member can post chat message"""
        post_chat_message(event=self.event, user=self.host, message="Hello!")

        msg = EventChatMessage.objects.get(event=self.event)
        self.assertEqual(msg.message, "Hello!")
        self.assertEqual(msg.author, self.host)

    def test_visitor_cannot_post_message(self):
        """Test that visitor cannot post chat message"""
        with self.assertRaises(ValueError) as context:
            post_chat_message(event=self.event, user=self.visitor, message="Hi!")

        self.assertIn("member", str(context.exception).lower())

    def test_empty_message_not_allowed(self):
        """Test that empty messages are not allowed"""
        with self.assertRaises(ValueError):
            post_chat_message(event=self.event, user=self.host, message="   ")

    def test_long_message_not_allowed(self):
        """Test that messages over 300 chars are not allowed"""
        long_message = "a" * 301
        with self.assertRaises(ValueError):
            post_chat_message(event=self.event, user=self.host, message=long_message)

    def test_message_retention_limit(self):
        """Test that only 20 messages are retained"""
        # Create 25 messages
        for i in range(25):
            post_chat_message(event=self.event, user=self.host, message=f"Message {i}")

        # Should only have 20 messages
        count = EventChatMessage.objects.filter(event=self.event).count()
        self.assertEqual(count, 20)

        # Should have the latest 20 messages
        messages = list(
            EventChatMessage.objects.filter(event=self.event).order_by("created_at")
        )
        # Check we have exactly 20 messages
        self.assertEqual(len(messages), 20)
        # The last message should definitely be Message 24
        self.assertEqual(messages[-1].message, "Message 24")
        # The first retained message should be from the later batch
        # Could be 4, 5, or 6 depending on when deletion happens
        first_msg_num = int(messages[0].message.split()[-1])
        self.assertGreaterEqual(first_msg_num, 4)
        self.assertLessEqual(first_msg_num, 6)


class JoinRequestServiceTests(TestCase):
    """Test join request services"""

    def setUp(self):
        self.host = User.objects.create_user(
            username="host", email="host@test.com", password="testpass123"
        )
        self.requester = User.objects.create_user(
            username="requester", email="requester@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Invite Event",
            host=self.host,
            visibility=EventVisibility.PUBLIC_INVITE,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

    def test_request_join(self):
        """Test creating a join request"""
        request_join(event=self.event, user=self.requester)

        self.assertTrue(
            EventJoinRequest.objects.filter(
                event=self.event,
                requester=self.requester,
                status=JoinRequestStatus.PENDING,
            ).exists()
        )

    def test_cannot_request_join_public_open(self):
        """Test cannot request join for PUBLIC_OPEN events"""
        open_event = Event.objects.create(
            title="Open Event",
            host=self.host,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

        with self.assertRaises(ValueError):
            request_join(event=open_event, user=self.requester)

    def test_cannot_request_join_if_member(self):
        """Test cannot request join if already a member"""
        EventMembership.objects.create(
            event=self.event, user=self.requester, role=MembershipRole.ATTENDEE
        )

        with self.assertRaises(ValueError) as context:
            request_join(event=self.event, user=self.requester)

        self.assertIn("member", str(context.exception).lower())

    def test_approve_join_request(self):
        """Test approving a join request"""
        join_req = EventJoinRequest.objects.create(
            event=self.event,
            requester=self.requester,
            status=JoinRequestStatus.PENDING,
        )

        approve_join_request(join_request=join_req)

        join_req.refresh_from_db()
        self.assertEqual(join_req.status, JoinRequestStatus.APPROVED)
        self.assertIsNotNone(join_req.decided_at)

        # User should be added as attendee
        self.assertTrue(
            EventMembership.objects.filter(
                event=self.event, user=self.requester, role=MembershipRole.ATTENDEE
            ).exists()
        )

    def test_decline_join_request(self):
        """Test declining a join request"""
        join_req = EventJoinRequest.objects.create(
            event=self.event,
            requester=self.requester,
            status=JoinRequestStatus.PENDING,
        )

        decline_join_request(join_request=join_req)

        join_req.refresh_from_db()
        self.assertEqual(join_req.status, JoinRequestStatus.DECLINED)
        self.assertIsNotNone(join_req.decided_at)


class UpdateEventServiceTests(TestCase):
    """Test update_event service"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.location1 = PublicArt.objects.create(
            title="Art 1", latitude=40.7128, longitude=-74.0060
        )
        self.location2 = PublicArt.objects.create(
            title="Art 2", latitude=40.7589, longitude=-73.9851
        )
        self.event = Event.objects.create(
            title="Original Title",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location1,
            description="Original description",
        )

    def test_update_event_title(self):
        """Test updating event title"""
        from events.forms import EventForm

        form_data = {
            "title": "Updated Title",
            "start_time": self.event.start_time,
            "start_location": self.location1,
            "visibility": EventVisibility.PUBLIC_OPEN,
            "description": self.event.description,
        }
        form = EventForm(data=form_data, instance=self.event)
        self.assertTrue(form.is_valid())

        updated_event = update_event(
            event=self.event, form=form, locations=[], invites=[]
        )

        self.assertEqual(updated_event.title, "Updated Title")

    def test_update_event_locations(self):
        """Test updating event locations"""
        from events.forms import EventForm

        # Add initial location
        EventLocation.objects.create(event=self.event, location=self.location1, order=1)

        form_data = {
            "title": self.event.title,
            "start_time": self.event.start_time,
            "start_location": self.location1,
            "visibility": self.event.visibility,
            "description": self.event.description,
        }
        form = EventForm(data=form_data, instance=self.event)
        self.assertTrue(form.is_valid())

        # Update with new location
        update_event(
            event=self.event, form=form, locations=[self.location2.id], invites=[]
        )

        # Old locations should be replaced
        self.assertEqual(EventLocation.objects.filter(event=self.event).count(), 1)
        loc = EventLocation.objects.get(event=self.event)
        self.assertEqual(loc.location, self.location2)


class DeleteEventServiceTests(TestCase):
    """Test delete_event service"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

    def test_delete_event(self):
        """Test soft deleting an event"""
        delete_event(event=self.event)

        self.event.refresh_from_db()
        self.assertTrue(self.event.is_deleted)


class LeaveEventServiceTests(TestCase):
    """Test leave_event service"""

    def setUp(self):
        self.host = User.objects.create_user(
            username="host", email="host@test.com", password="testpass123"
        )
        self.attendee = User.objects.create_user(
            username="attendee", email="attendee@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.host,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        EventMembership.objects.create(
            event=self.event, user=self.host, role=MembershipRole.HOST
        )
        EventMembership.objects.create(
            event=self.event, user=self.attendee, role=MembershipRole.ATTENDEE
        )

    def test_attendee_can_leave(self):
        """Test that attendee can leave event"""
        leave_event(event=self.event, user=self.attendee)

        self.assertFalse(
            EventMembership.objects.filter(
                event=self.event, user=self.attendee
            ).exists()
        )

    def test_host_cannot_leave(self):
        """Test that host cannot leave their own event"""
        with self.assertRaises(ValueError) as context:
            leave_event(event=self.event, user=self.host)

        self.assertIn("host", str(context.exception).lower())


class FavoriteServiceTests(TestCase):
    """Test favorite_event and unfavorite_event services"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

    def test_favorite_event(self):
        """Test favoriting an event"""
        favorite_event(event=self.event, user=self.user)

        self.assertTrue(
            EventFavorite.objects.filter(event=self.event, user=self.user).exists()
        )

    def test_favorite_event_idempotent(self):
        """Test that favoriting twice doesn't cause error"""
        favorite_event(event=self.event, user=self.user)
        favorite_event(event=self.event, user=self.user)  # Should not raise error

        self.assertEqual(
            EventFavorite.objects.filter(event=self.event, user=self.user).count(), 1
        )

    def test_cannot_favorite_deleted_event(self):
        """Test cannot favorite a deleted event"""
        self.event.is_deleted = True
        self.event.save()

        with self.assertRaises(ValueError):
            favorite_event(event=self.event, user=self.user)

    def test_unfavorite_event(self):
        """Test unfavoriting an event"""
        EventFavorite.objects.create(event=self.event, user=self.user)

        result = unfavorite_event(event=self.event, user=self.user)

        self.assertTrue(result)
        self.assertFalse(
            EventFavorite.objects.filter(event=self.event, user=self.user).exists()
        )

    def test_unfavorite_non_favorited_event(self):
        """Test unfavoriting an event that wasn't favorited"""
        result = unfavorite_event(event=self.event, user=self.user)

        self.assertFalse(result)


# Selector tests continue in next part due to length...
