"""
Comprehensive test suite for Events app - Part 2
Tests selectors, forms, and views
"""

from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json

from events.models import (
    Event,
    EventMembership,
    EventChatMessage,
    EventFavorite,
)
from events.enums import (
    EventVisibility,
    MembershipRole,
)
from events.selectors import (
    search_locations,
    search_users,
    public_event_pins,
    list_public_events,
    user_has_joined,
    user_role_in_event,
    list_chat_messages,
)
from events.forms import EventForm, parse_locations, parse_invites
from loc_detail.models import PublicArt


class SearchLocationsSelectorTests(TestCase):
    """Test search_locations selector"""

    def setUp(self):
        self.location1 = PublicArt.objects.create(
            title="Statue of Liberty",
            artist_name="Frederic Auguste Bartholdi",
            location="Liberty Island",
            latitude=40.6892,
            longitude=-74.0445,
        )
        self.location2 = PublicArt.objects.create(
            title="Brooklyn Bridge",
            artist_name="John Roebling",
            location="Brooklyn",
            latitude=40.7061,
            longitude=-73.9969,
        )
        self.location3 = PublicArt.objects.create(
            title="Central Park Fountain",
            artist_name="Unknown",
            location="Central Park",
            latitude=40.7829,
            longitude=-73.9654,
        )

    def test_search_by_title(self):
        """Test searching locations by title"""
        results = list(search_locations("statue", limit=10))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Statue of Liberty")

    def test_search_by_artist(self):
        """Test searching locations by artist"""
        results = list(search_locations("roebling", limit=10))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Brooklyn Bridge")

    def test_search_by_location(self):
        """Test searching locations by location field"""
        results = list(search_locations("park", limit=10))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Central Park Fountain")

    def test_search_case_insensitive(self):
        """Test that search is case insensitive"""
        results = list(search_locations("BROOKLYN", limit=10))
        self.assertEqual(len(results), 1)

    def test_search_limit(self):
        """Test that limit parameter works"""
        # Create 15 more locations
        for i in range(15):
            PublicArt.objects.create(
                title=f"Test Art {i}",
                latitude=40.0 + i * 0.1,
                longitude=-74.0 + i * 0.1,
            )

        results = list(search_locations("test", limit=5))
        self.assertEqual(len(results), 5)


class SearchUsersSelectorTests(TestCase):
    """Test search_users selector"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="johndoe", email="john@example.com", password="pass123"
        )
        self.user2 = User.objects.create_user(
            username="janedoe", email="jane@example.com", password="pass123"
        )
        self.user3 = User.objects.create_user(
            username="alice", email="alice@wonderland.com", password="pass123"
        )

    def test_search_by_username(self):
        """Test searching users by username"""
        results = list(search_users("john", limit=10))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["username"], "johndoe")

    def test_search_by_email(self):
        """Test searching users by email"""
        results = list(search_users("wonderland", limit=10))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["username"], "alice")

    def test_search_partial_match(self):
        """Test partial matching"""
        results = list(search_users("doe", limit=10))
        self.assertEqual(len(results), 2)


class PublicEventPinsSelectorTests(TestCase):
    """Test public_event_pins selector"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="pass123"
        )
        self.location1 = PublicArt.objects.create(
            title="Art 1", latitude=40.7128, longitude=-74.0060
        )
        self.location2 = PublicArt.objects.create(
            title="Art 2", latitude=40.7589, longitude=-73.9851
        )

    def test_includes_public_open_events(self):
        """Test that PUBLIC_OPEN events are included"""
        Event.objects.create(
            title="Public Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location1,
        )

        pins = list(public_event_pins())
        self.assertEqual(len(pins), 1)
        self.assertEqual(pins[0]["title"], "Public Event")

    def test_includes_public_invite_events(self):
        """Test that PUBLIC_INVITE events are included"""
        Event.objects.create(
            title="Invite Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_INVITE,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location1,
        )

        pins = list(public_event_pins())
        self.assertEqual(len(pins), 1)

    def test_excludes_private_events(self):
        """Test that PRIVATE events are excluded"""
        Event.objects.create(
            title="Private Event",
            host=self.user,
            visibility=EventVisibility.PRIVATE,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location1,
        )

        pins = list(public_event_pins())
        self.assertEqual(len(pins), 0)

    def test_excludes_deleted_events(self):
        """Test that deleted events are excluded"""
        Event.objects.create(
            title="Deleted Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location1,
            is_deleted=True,
        )

        pins = list(public_event_pins())
        self.assertEqual(len(pins), 0)


class ListPublicEventsSelectorTests(TestCase):
    """Test list_public_events selector"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="pass123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art", latitude=40.7128, longitude=-74.0060
        )

    def test_lists_public_events(self):
        """Test listing all public events"""
        Event.objects.create(
            title="Event 1",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        Event.objects.create(
            title="Event 2",
            host=self.user,
            visibility=EventVisibility.PUBLIC_INVITE,
            start_time=timezone.now() + timedelta(days=2),
            start_location=self.location,
        )

        events = list(list_public_events())
        self.assertEqual(len(events), 2)

    def test_search_filter(self):
        """Test search filtering"""
        Event.objects.create(
            title="Python Workshop",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        Event.objects.create(
            title="Django Meetup",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=2),
            start_location=self.location,
        )

        events = list(list_public_events(query="python"))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].title, "Python Workshop")

    def test_visibility_filter_open(self):
        """Test filtering by visibility=open"""
        Event.objects.create(
            title="Open Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        Event.objects.create(
            title="Invite Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_INVITE,
            start_time=timezone.now() + timedelta(days=2),
            start_location=self.location,
        )

        events = list(list_public_events(visibility_filter="open"))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].title, "Open Event")

    def test_visibility_filter_invite(self):
        """Test filtering by visibility=invite"""
        Event.objects.create(
            title="Open Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        Event.objects.create(
            title="Invite Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_INVITE,
            start_time=timezone.now() + timedelta(days=2),
            start_location=self.location,
        )

        events = list(list_public_events(visibility_filter="invite"))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].title, "Invite Event")

    def test_ordering(self):
        """Test ordering by start_time"""
        Event.objects.create(
            title="Later Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=2),
            start_location=self.location,
        )
        Event.objects.create(
            title="Earlier Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

        # Ascending order
        events = list(list_public_events(order="start_time"))
        self.assertEqual(events[0].title, "Earlier Event")

        # Descending order
        events = list(list_public_events(order="-start_time"))
        self.assertEqual(events[0].title, "Later Event")


class UserHasJoinedSelectorTests(TestCase):
    """Test user_has_joined selector"""

    def setUp(self):
        self.host = User.objects.create_user(
            username="host", email="host@test.com", password="pass123"
        )
        self.attendee = User.objects.create_user(
            username="attendee", email="attendee@test.com", password="pass123"
        )
        self.visitor = User.objects.create_user(
            username="visitor", email="visitor@test.com", password="pass123"
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

    def test_host_has_joined(self):
        """Test that host is considered joined"""
        self.assertTrue(user_has_joined(self.event, self.host))

    def test_attendee_has_joined(self):
        """Test that attendee is considered joined"""
        self.assertTrue(user_has_joined(self.event, self.attendee))

    def test_visitor_has_not_joined(self):
        """Test that visitor is not considered joined"""
        self.assertFalse(user_has_joined(self.event, self.visitor))


class UserRoleInEventSelectorTests(TestCase):
    """Test user_role_in_event selector"""

    def setUp(self):
        self.host = User.objects.create_user(
            username="host", email="host@test.com", password="pass123"
        )
        self.attendee = User.objects.create_user(
            username="attendee", email="attendee@test.com", password="pass123"
        )
        self.visitor = User.objects.create_user(
            username="visitor", email="visitor@test.com", password="pass123"
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
            event=self.event, user=self.attendee, role=MembershipRole.ATTENDEE
        )

    def test_host_role(self):
        """Test that host gets HOST role"""
        role = user_role_in_event(self.event, self.host)
        self.assertEqual(role, "HOST")

    def test_attendee_role(self):
        """Test that attendee gets ATTENDEE role"""
        role = user_role_in_event(self.event, self.attendee)
        self.assertEqual(role, "ATTENDEE")

    def test_visitor_role(self):
        """Test that visitor gets VISITOR role"""
        role = user_role_in_event(self.event, self.visitor)
        self.assertEqual(role, "VISITOR")


class ListChatMessagesSelectorTests(TestCase):
    """Test list_chat_messages selector"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="pass123"
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

    def test_returns_messages_oldest_first(self):
        """Test that messages are returned oldest first"""
        import time

        EventChatMessage.objects.create(
            event=self.event, author=self.user, message="First"
        )
        time.sleep(0.01)
        EventChatMessage.objects.create(
            event=self.event, author=self.user, message="Second"
        )
        time.sleep(0.01)
        EventChatMessage.objects.create(
            event=self.event, author=self.user, message="Third"
        )

        messages = list_chat_messages(self.event, limit=20)
        self.assertEqual(messages[0].message, "First")
        self.assertEqual(messages[1].message, "Second")
        self.assertEqual(messages[2].message, "Third")

    def test_respects_limit(self):
        """Test that limit parameter is respected"""
        for i in range(25):
            EventChatMessage.objects.create(
                event=self.event, author=self.user, message=f"Message {i}"
            )

        messages = list_chat_messages(self.event, limit=10)
        self.assertEqual(len(messages), 10)


class EventFormTests(TestCase):
    """Test EventForm"""

    def setUp(self):
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )

    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {
            "title": "Test Event",
            "start_time": timezone.now() + timedelta(days=1),
            "start_location": self.location.id,
            "visibility": EventVisibility.PUBLIC_OPEN,
            "description": "Test description",
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_title_too_long(self):
        """Test that title over 80 chars is rejected"""
        form_data = {
            "title": "A" * 81,
            "start_time": timezone.now() + timedelta(days=1),
            "start_location": self.location.id,
            "visibility": EventVisibility.PUBLIC_OPEN,
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_past_start_time_rejected(self):
        """Test that past start_time is rejected"""
        form_data = {
            "title": "Test Event",
            "start_time": timezone.now() - timedelta(days=1),
            "start_location": self.location.id,
            "visibility": EventVisibility.PUBLIC_OPEN,
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("start_time", form.errors)


class ParseHelperTests(TestCase):
    """Test parse_locations and parse_invites helpers"""

    def test_parse_locations(self):
        """Test parsing location IDs from request"""
        factory = RequestFactory()
        request = factory.post("/", {"locations[]": ["1", "2", "3"]})
        locations = parse_locations(request)
        self.assertEqual(locations, [1, 2, 3])

    def test_parse_locations_filters_invalid(self):
        """Test that invalid location IDs are filtered"""
        factory = RequestFactory()
        request = factory.post("/", {"locations[]": ["1", "invalid", "3"]})
        locations = parse_locations(request)
        self.assertEqual(locations, [1, 3])

    def test_parse_invites(self):
        """Test parsing invite IDs from request"""
        factory = RequestFactory()
        request = factory.post("/", {"invites[]": ["5", "10", "15"]})
        invites = parse_invites(request)
        self.assertEqual(invites, [5, 10, 15])


class CreateEventViewTests(TestCase):
    """Test create event view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )

    def test_login_required(self):
        """Test that login is required"""
        response = self.client.get(reverse("events:create"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_get_create_form(self):
        """Test GET request shows form"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("events:create"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_post_create_event(self):
        """Test POST request creates event"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("events:create"),
            {
                "title": "New Event",
                "start_time": (timezone.now() + timedelta(days=1)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "start_location": self.location.id,
                "visibility": EventVisibility.PUBLIC_OPEN,
                "description": "Test",
            },
        )

        # Should redirect to event detail
        self.assertEqual(response.status_code, 302)

        # Event should be created
        event = Event.objects.get(title="New Event")
        self.assertEqual(event.host, self.user)


class DetailViewTests(TestCase):
    """Test event detail view"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(
            username="host", email="host@test.com", password="testpass123"
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

    def test_login_required(self):
        """Test that login is required"""
        response = self.client.get(
            reverse("events:detail", kwargs={"slug": self.event.slug})
        )
        self.assertEqual(response.status_code, 302)

    def test_detail_page_loads(self):
        """Test detail page loads successfully"""
        self.client.login(username="host", password="testpass123")
        response = self.client.get(
            reverse("events:detail", kwargs={"slug": self.event.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["event"], self.event)

    def test_host_sees_host_context(self):
        """Test that host sees appropriate context"""
        EventMembership.objects.create(
            event=self.event, user=self.host, role=MembershipRole.HOST
        )
        self.client.login(username="host", password="testpass123")
        response = self.client.get(
            reverse("events:detail", kwargs={"slug": self.event.slug})
        )
        self.assertEqual(response.context["user_role"], "HOST")

    def test_deleted_event_redirects(self):
        """Test that deleted events redirect"""
        self.event.is_deleted = True
        self.event.save()

        self.client.login(username="visitor", password="testpass123")
        response = self.client.get(
            reverse("events:detail", kwargs={"slug": self.event.slug})
        )
        self.assertEqual(response.status_code, 302)


class PublicEventsViewTests(TestCase):
    """Test public events list view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )

    def test_login_required(self):
        """Test that login is required"""
        response = self.client.get(reverse("events:public"))
        self.assertEqual(response.status_code, 302)

    def test_public_events_list(self):
        """Test public events are listed"""
        Event.objects.create(
            title="Public Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("events:public"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("page_obj", response.context)

    def test_search_filter(self):
        """Test search filtering works"""
        Event.objects.create(
            title="Python Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        Event.objects.create(
            title="Django Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=2),
            start_location=self.location,
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("events:public") + "?q=python")
        self.assertEqual(response.status_code, 200)


class JoinEventViewTests(TestCase):
    """Test join event view"""

    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(
            username="host", email="host@test.com", password="testpass123"
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

    def test_join_event_success(self):
        """Test successfully joining an event"""
        self.client.login(username="visitor", password="testpass123")
        response = self.client.post(
            reverse("events:join", kwargs={"slug": self.event.slug})
        )

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Membership should be created
        self.assertTrue(
            EventMembership.objects.filter(
                event=self.event, user=self.visitor, role=MembershipRole.ATTENDEE
            ).exists()
        )

    def test_join_requires_post(self):
        """Test that join requires POST"""
        self.client.login(username="visitor", password="testpass123")
        response = self.client.get(
            reverse("events:join", kwargs={"slug": self.event.slug})
        )
        self.assertEqual(response.status_code, 405)


class FavoritesViewTests(TestCase):
    """Test favorites view"""

    def setUp(self):
        self.client = Client()
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

    def test_favorites_page_loads(self):
        """Test favorites page loads"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("events:favorites"))
        self.assertEqual(response.status_code, 200)

    def test_favorite_event(self):
        """Test favoriting an event"""
        self.client.login(username="testuser", password="testpass123")
        self.client.post(reverse("events:favorite", kwargs={"slug": self.event.slug}))

        # Should create favorite
        self.assertTrue(
            EventFavorite.objects.filter(event=self.event, user=self.user).exists()
        )

    def test_unfavorite_event(self):
        """Test unfavoriting an event"""
        EventFavorite.objects.create(event=self.event, user=self.user)

        self.client.login(username="testuser", password="testpass123")
        self.client.post(reverse("events:unfavorite", kwargs={"slug": self.event.slug}))

        # Should remove favorite
        self.assertFalse(
            EventFavorite.objects.filter(event=self.event, user=self.user).exists()
        )


class APIViewTests(TestCase):
    """Test API views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
            latitude=40.7128,
            longitude=-74.0060,
        )

    def test_api_locations_search(self):
        """Test location search API"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("events:api_locations_search") + "?q=test")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 1)

    def test_api_users_search(self):
        """Test user search API"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("events:api_users_search") + "?q=test")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("results", data)

    def test_api_event_pins(self):
        """Test event pins API"""
        Event.objects.create(
            title="Test Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("events:api_event_pins"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("points", data)
        self.assertEqual(len(data["points"]), 1)
