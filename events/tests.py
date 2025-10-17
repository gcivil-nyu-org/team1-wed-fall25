from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from loc_detail.models import PublicArt
from .models import Event, EventLocation, EventMembership, EventInvite
from .enums import EventVisibility, MembershipRole, InviteStatus
from .services import create_event, join_event, accept_invite, decline_invite
from .selectors import list_public_events, user_has_joined, list_user_invitations
from .forms import EventForm


class EventModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.location = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
            latitude=40.7128,
            longitude=-74.0060,
        )

    def test_event_slug_generation(self):
        """Test that event slug is auto-generated"""
        future_time = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            title="Test Event",
            host=self.user,
            start_time=future_time,
            start_location=self.location,
        )

        self.assertIsNotNone(event.slug)
        self.assertIn("test-event", event.slug)

    def test_event_str(self):
        """Test event string representation"""
        future_time = timezone.now() + timedelta(days=1)
        event = Event.objects.create(
            title="Test Event",
            host=self.user,
            start_time=future_time,
            start_location=self.location,
        )

        expected = f"Test Event by {self.user.username}"
        self.assertEqual(str(event), expected)


class EventServiceTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username="host", password="testpass")
        self.invitee1 = User.objects.create_user(
            username="invitee1", password="testpass"
        )
        self.invitee2 = User.objects.create_user(
            username="invitee2", password="testpass"
        )

        self.location1 = PublicArt.objects.create(
            title="Art 1", artist_name="Artist 1", latitude=40.7128, longitude=-74.0060
        )
        self.location2 = PublicArt.objects.create(
            title="Art 2", artist_name="Artist 2", latitude=40.7589, longitude=-73.9851
        )

    def test_create_event_basic(self):
        """Test creating a basic event"""
        future_time = timezone.now() + timedelta(days=1)

        form_data = {
            "title": "Test Event",
            "start_time": future_time,
            "start_location": self.location1,
            "visibility": EventVisibility.PUBLIC_OPEN,
            "description": "Test description",
        }

        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

        event = create_event(host=self.host, form=form, locations=[], invites=[])

        self.assertEqual(event.title, "Test Event")
        self.assertEqual(event.host, self.host)
        self.assertEqual(event.visibility, EventVisibility.PUBLIC_OPEN)

        # Check host membership created
        self.assertTrue(
            EventMembership.objects.filter(
                event=event, user=self.host, role=MembershipRole.HOST
            ).exists()
        )

    def test_create_event_with_locations(self):
        """Test creating event with additional locations"""
        future_time = timezone.now() + timedelta(days=1)

        form_data = {
            "title": "Multi-Stop Event",
            "start_time": future_time,
            "start_location": self.location1,
            "visibility": EventVisibility.PUBLIC_OPEN,
            "description": "",
        }

        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

        event = create_event(
            host=self.host, form=form, locations=[self.location2.id], invites=[]
        )

        # Check location created
        self.assertEqual(event.locations.count(), 1)
        self.assertEqual(event.locations.first().location, self.location2)
        self.assertEqual(event.locations.first().order, 1)

    def test_create_event_with_invites(self):
        """Test creating event with invites"""
        future_time = timezone.now() + timedelta(days=1)

        form_data = {
            "title": "Private Event",
            "start_time": future_time,
            "start_location": self.location1,
            "visibility": EventVisibility.PRIVATE,
            "description": "",
        }

        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

        event = create_event(
            host=self.host,
            form=form,
            locations=[],
            invites=[self.invitee1.id, self.invitee2.id],
        )

        # Check invites created
        self.assertEqual(event.invites.count(), 2)
        self.assertTrue(
            EventInvite.objects.filter(
                event=event, invitee=self.invitee1, status=InviteStatus.PENDING
            ).exists()
        )

        # Check invited memberships created
        self.assertEqual(
            event.memberships.filter(role=MembershipRole.INVITED).count(), 2
        )


class EventFormTests(TestCase):
    def setUp(self):
        self.location = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
            latitude=40.7128,
            longitude=-74.0060,
        )

    def test_form_valid_data(self):
        """Test form with valid data"""
        future_time = timezone.now() + timedelta(days=1)

        form = EventForm(
            data={
                "title": "Valid Event",
                "start_time": future_time,
                "start_location": self.location.id,
                "visibility": EventVisibility.PUBLIC_OPEN,
                "description": "Valid description",
            }
        )

        self.assertTrue(form.is_valid())

    def test_form_past_time_invalid(self):
        """Test form rejects past datetime"""
        past_time = timezone.now() - timedelta(days=1)

        form = EventForm(
            data={
                "title": "Past Event",
                "start_time": past_time,
                "start_location": self.location.id,
                "visibility": EventVisibility.PUBLIC_OPEN,
                "description": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("start_time", form.errors)


# PHASE 2 TESTS


class PublicEventsTests(TestCase):
    """Test public events listing and filtering"""

    def setUp(self):
        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            artist_name="Artist",
            latitude=40.7128,
            longitude=-74.0060,
        )

        future_time = timezone.now() + timedelta(days=1)

        # Create public open event
        self.public_open = Event.objects.create(
            title="Public Open Event",
            host=self.user1,
            start_time=future_time,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )

        # Create public invite event
        self.public_invite = Event.objects.create(
            title="Public Invite Event",
            host=self.user1,
            start_time=future_time,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_INVITE,
        )

        # Create private event
        self.private = Event.objects.create(
            title="Private Event",
            host=self.user1,
            start_time=future_time,
            start_location=self.location,
            visibility=EventVisibility.PRIVATE,
        )

    def test_list_public_events_excludes_private(self):
        """Private events should not appear in public list"""
        events = list_public_events()

        self.assertEqual(events.count(), 2)
        self.assertIn(self.public_open, events)
        self.assertIn(self.public_invite, events)
        self.assertNotIn(self.private, events)

    def test_search_filters_by_query(self):
        """Search should filter by title, host, location"""
        # Search by title
        events = list_public_events(query="Open")
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.first(), self.public_open)

        # Search by host username
        events = list_public_events(query="user1")
        self.assertEqual(events.count(), 2)

    def test_visibility_filter(self):
        """Visibility filter should work"""
        # Filter open events
        events = list_public_events(visibility_filter="open")
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.first(), self.public_open)

        # Filter invite events
        events = list_public_events(visibility_filter="invite")
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.first(), self.public_invite)

    def test_user_has_joined(self):
        """Test checking if user has joined event"""
        # User hasn't joined
        self.assertFalse(user_has_joined(self.public_open, self.user2))

        # Create membership
        EventMembership.objects.create(
            event=self.public_open, user=self.user2, role=MembershipRole.ATTENDEE
        )

        # User has joined
        self.assertTrue(user_has_joined(self.public_open, self.user2))


class JoinEventTests(TestCase):
    """Test joining events"""

    def setUp(self):
        self.host = User.objects.create_user(username="host", password="pass")
        self.user = User.objects.create_user(username="user", password="pass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            artist_name="Artist",
            latitude=40.7128,
            longitude=-74.0060,
        )

        future_time = timezone.now() + timedelta(days=1)

        self.public_open = Event.objects.create(
            title="Public Open",
            host=self.host,
            start_time=future_time,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_OPEN,
        )

        self.public_invite = Event.objects.create(
            title="Public Invite",
            host=self.host,
            start_time=future_time,
            start_location=self.location,
            visibility=EventVisibility.PUBLIC_INVITE,
        )

        self.private = Event.objects.create(
            title="Private",
            host=self.host,
            start_time=future_time,
            start_location=self.location,
            visibility=EventVisibility.PRIVATE,
        )

    def test_join_public_open_event(self):
        """Anyone can join PUBLIC_OPEN events"""
        join_event(event=self.public_open, user=self.user)

        # Verify membership created
        self.assertTrue(
            EventMembership.objects.filter(
                event=self.public_open, user=self.user, role=MembershipRole.ATTENDEE
            ).exists()
        )

    def test_join_public_invite_requires_invite(self):
        """PUBLIC_INVITE requires invitation"""
        # Try to join without invite
        with self.assertRaises(ValueError):
            join_event(event=self.public_invite, user=self.user)

        # Create invite
        EventInvite.objects.create(
            event=self.public_invite,
            invited_by=self.host,
            invitee=self.user,
            status=InviteStatus.PENDING,
        )

        # Now join should succeed
        join_event(event=self.public_invite, user=self.user)
        self.assertTrue(
            EventMembership.objects.filter(
                event=self.public_invite, user=self.user, role=MembershipRole.ATTENDEE
            ).exists()
        )

    def test_cannot_join_private(self):
        """Cannot join PRIVATE events"""
        with self.assertRaises(ValueError):
            join_event(event=self.private, user=self.user)

    def test_cannot_join_twice(self):
        """Cannot join event twice"""
        join_event(event=self.public_open, user=self.user)

        with self.assertRaises(ValueError):
            join_event(event=self.public_open, user=self.user)


class InvitationTests(TestCase):
    """Test invitation accept/decline"""

    def setUp(self):
        self.host = User.objects.create_user(username="host", password="pass")
        self.invitee = User.objects.create_user(username="invitee", password="pass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            artist_name="Artist",
            latitude=40.7128,
            longitude=-74.0060,
        )

        future_time = timezone.now() + timedelta(days=1)

        self.event = Event.objects.create(
            title="Private Event",
            host=self.host,
            start_time=future_time,
            start_location=self.location,
            visibility=EventVisibility.PRIVATE,
        )

        self.invite = EventInvite.objects.create(
            event=self.event,
            invited_by=self.host,
            invitee=self.invitee,
            status=InviteStatus.PENDING,
        )

        # Create invited membership
        EventMembership.objects.create(
            event=self.event, user=self.invitee, role=MembershipRole.INVITED
        )

    def test_accept_invite_creates_membership(self):
        """Accepting invite creates ATTENDEE membership"""
        accept_invite(invite=self.invite)

        # Check invite status updated
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, InviteStatus.ACCEPTED)
        self.assertIsNotNone(self.invite.responded_at)

        # Check membership updated to ATTENDEE
        membership = EventMembership.objects.get(event=self.event, user=self.invitee)
        self.assertEqual(membership.role, MembershipRole.ATTENDEE)

    def test_decline_invite_removes_membership(self):
        """Declining invite removes INVITED membership"""
        decline_invite(invite=self.invite)

        # Check invite status updated
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, InviteStatus.DECLINED)
        self.assertIsNotNone(self.invite.responded_at)

        # Check membership removed
        self.assertFalse(
            EventMembership.objects.filter(
                event=self.event, user=self.invitee, role=MembershipRole.INVITED
            ).exists()
        )

    def test_list_user_invitations(self):
        """Test fetching user's pending invitations"""
        invites = list_user_invitations(self.invitee)

        self.assertEqual(invites.count(), 1)
        self.assertEqual(invites.first(), self.invite)

        # After accepting, should not appear
        accept_invite(invite=self.invite)
        invites = list_user_invitations(self.invitee)
        self.assertEqual(invites.count(), 0)
