"""
Tests for the unified favorites app
Tests the consolidated favorites view with tabs for art, events, and itineraries
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import datetime, timedelta
from loc_detail.models import PublicArt, UserFavoriteArt
from events.models import Event, EventFavorite
from itineraries.models import Itinerary, ItineraryStop, ItineraryFavorite


class UnifiedFavoritesViewTests(TestCase):
    """Tests for the unified favorites view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_favorites_requires_login(self):
        """Test that favorites view requires login"""
        response = self.client.get(reverse("favorites:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_favorites_view_authenticated(self):
        """Test favorites view for authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "favorites/index.html")

    def test_favorites_default_tab_is_art(self):
        """Test that default tab is art"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index"))
        self.assertEqual(response.context["active_tab"], "art")

    def test_favorites_art_tab(self):
        """Test art favorites tab"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=art")
        self.assertEqual(response.context["active_tab"], "art")
        self.assertIn("page_obj", response.context)

    def test_favorites_events_tab(self):
        """Test events favorites tab"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=events")
        self.assertEqual(response.context["active_tab"], "events")
        self.assertIn("page_obj", response.context)

    def test_favorites_itineraries_tab(self):
        """Test itineraries favorites tab"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=itineraries")
        self.assertEqual(response.context["active_tab"], "itineraries")
        self.assertIn("itineraries", response.context)


class ArtFavoritesTabTests(TestCase):
    """Tests for art favorites tab functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.art1 = PublicArt.objects.create(
            title="Art 1",
            artist_name="Artist A",
            borough="Manhattan",
            latitude=Decimal("40.7580"),
            longitude=Decimal("-73.9855"),
            external_id="art001",
        )
        self.art2 = PublicArt.objects.create(
            title="Art 2",
            artist_name="Artist B",
            borough="Brooklyn",
            latitude=Decimal("40.6782"),
            longitude=Decimal("-73.9442"),
            external_id="art002",
        )

    def test_art_tab_empty(self):
        """Test art tab with no favorites"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=art")
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 0)

    def test_art_tab_with_favorites(self):
        """Test art tab with favorites"""
        UserFavoriteArt.objects.create(user=self.user, art=self.art1)
        UserFavoriteArt.objects.create(user=self.user, art=self.art2)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=art")
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 2)

    def test_art_tab_search(self):
        """Test art tab search functionality"""
        UserFavoriteArt.objects.create(user=self.user, art=self.art1)
        UserFavoriteArt.objects.create(user=self.user, art=self.art2)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=art&search=Art 1")
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 1)
        self.assertEqual(page_obj[0].art.title, "Art 1")

    def test_art_tab_borough_filter(self):
        """Test art tab borough filter"""
        UserFavoriteArt.objects.create(user=self.user, art=self.art1)
        UserFavoriteArt.objects.create(user=self.user, art=self.art2)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("favorites:index") + "?tab=art&borough=Manhattan"
        )
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 1)
        self.assertEqual(page_obj[0].art.borough, "Manhattan")

    def test_art_tab_search_by_artist(self):
        """Test searching by artist name"""
        UserFavoriteArt.objects.create(user=self.user, art=self.art1)
        UserFavoriteArt.objects.create(user=self.user, art=self.art2)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("favorites:index") + "?tab=art&search=Artist B"
        )
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 1)
        self.assertEqual(page_obj[0].art.artist_name, "Artist B")

    def test_art_tab_boroughs_list(self):
        """Test that boroughs list is populated"""
        UserFavoriteArt.objects.create(user=self.user, art=self.art1)
        UserFavoriteArt.objects.create(user=self.user, art=self.art2)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=art")
        boroughs = response.context["boroughs"]
        self.assertIn("Manhattan", boroughs)
        self.assertIn("Brooklyn", boroughs)

    def test_art_tab_pagination(self):
        """Test art tab pagination"""
        # Create 25 art pieces to test pagination (page size is 20)
        for i in range(25):
            art = PublicArt.objects.create(
                title=f"Art {i}",
                latitude=Decimal("40.7580") + Decimal(str(i * 0.001)),
                longitude=Decimal("-73.9855") + Decimal(str(i * 0.001)),
                external_id=f"artpaginate{i:03d}",
            )
            UserFavoriteArt.objects.create(user=self.user, art=art)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=art")
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 20)  # First page
        self.assertTrue(page_obj.has_next())

        # Test second page
        response = self.client.get(reverse("favorites:index") + "?tab=art&page=2")
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 5)  # Remaining items
        self.assertFalse(page_obj.has_next())


class EventsFavoritesTabTests(TestCase):
    """Tests for events favorites tab functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.host = User.objects.create_user(username="host", password="testpass123")
        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=Decimal("40.7580"),
            longitude=Decimal("-73.9855"),
            external_id="loc001",
        )
        self.event1 = Event.objects.create(
            title="Event 1",
            description="First event",
            host=self.host,
            start_location=self.location,
            start_time=datetime.now() + timedelta(days=1),
        )
        self.event2 = Event.objects.create(
            title="Event 2",
            description="Second event",
            host=self.host,
            start_location=self.location,
            start_time=datetime.now() + timedelta(days=2),
        )

    def test_events_tab_empty(self):
        """Test events tab with no favorites"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=events")
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 0)

    def test_events_tab_with_favorites(self):
        """Test events tab with favorites"""
        EventFavorite.objects.create(user=self.user, event=self.event1)
        EventFavorite.objects.create(user=self.user, event=self.event2)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=events")
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 2)

    def test_events_tab_excludes_deleted(self):
        """Test that deleted events are excluded"""
        EventFavorite.objects.create(user=self.user, event=self.event1)
        EventFavorite.objects.create(user=self.user, event=self.event2)

        # Mark event1 as deleted
        self.event1.is_deleted = True
        self.event1.save()

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=events")
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 1)
        self.assertEqual(page_obj[0].title, "Event 2")

    def test_events_tab_shows_joined_status(self):
        """Test that events show joined status"""
        from events.models import EventMembership
        from events.enums import MembershipRole

        EventFavorite.objects.create(user=self.user, event=self.event1)
        # User joins the event via membership
        EventMembership.objects.create(
            event=self.event1, user=self.user, role=MembershipRole.ATTENDEE
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=events")
        page_obj = response.context["page_obj"]
        self.assertTrue(page_obj[0].joined)

    def test_events_tab_pagination(self):
        """Test events tab pagination"""
        # Create 15 events to test pagination (page size is 12)
        for i in range(15):
            event = Event.objects.create(
                title=f"Event {i}",
                host=self.host,
                start_location=self.location,
                start_time=datetime.now() + timedelta(days=i),
            )
            EventFavorite.objects.create(user=self.user, event=event)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=events")
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 12)  # First page
        self.assertTrue(page_obj.has_next())


class ItinerariesFavoritesTabTests(TestCase):
    """Tests for itineraries favorites tab functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=Decimal("40.7580"),
            longitude=Decimal("-73.9855"),
            external_id="loc001",
        )
        self.itinerary1 = Itinerary.objects.create(
            user=self.user, title="My Tour", description="My tour"
        )
        self.itinerary2 = Itinerary.objects.create(
            user=self.other_user, title="Other Tour", description="Other's tour"
        )

    def test_itineraries_tab_empty(self):
        """Test itineraries tab with no favorites"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=itineraries")
        itineraries = response.context["itineraries"]
        self.assertEqual(len(itineraries), 0)

    def test_itineraries_tab_with_favorites(self):
        """Test itineraries tab with favorites"""
        ItineraryFavorite.objects.create(user=self.user, itinerary=self.itinerary1)
        ItineraryFavorite.objects.create(user=self.user, itinerary=self.itinerary2)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=itineraries")
        itineraries = response.context["itineraries"]
        self.assertEqual(len(itineraries), 2)

    def test_itineraries_tab_shows_stops(self):
        """Test that itineraries show their stops"""
        ItineraryStop.objects.create(
            itinerary=self.itinerary1, location=self.location, order=1
        )
        ItineraryFavorite.objects.create(user=self.user, itinerary=self.itinerary1)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=itineraries")
        itineraries = response.context["itineraries"]
        self.assertEqual(itineraries[0].stops.count(), 1)

    def test_itineraries_tab_has_favorited_at(self):
        """Test that itineraries have favorited_at timestamp"""
        fav = ItineraryFavorite.objects.create(
            user=self.user, itinerary=self.itinerary1
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=itineraries")
        itineraries = response.context["itineraries"]
        self.assertEqual(itineraries[0].favorited_at, fav.created_at)


class FavoritesRedirectTests(TestCase):
    """Tests for redirects from old favorites URLs"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_art_favorites_redirect(self):
        """Test redirect from old art favorites URL"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/loc_detail/favorites/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/favorites/", response.url)
        self.assertIn("tab=art", response.url)

    def test_events_favorites_redirect(self):
        """Test redirect from old events favorites URL"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/events/favorites/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/favorites/", response.url)
        self.assertIn("tab=events", response.url)

    def test_itineraries_favorites_redirect(self):
        """Test redirect from old itineraries favorites URL"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get("/itineraries/favorites/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/favorites/", response.url)
        self.assertIn("tab=itineraries", response.url)


class FavoritesIntegrationTests(TestCase):
    """Integration tests for favorites functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.host = User.objects.create_user(username="host", password="testpass123")

        # Create test data
        self.art = PublicArt.objects.create(
            title="Test Art",
            latitude=Decimal("40.7580"),
            longitude=Decimal("-73.9855"),
            external_id="art001",
        )
        self.event = Event.objects.create(
            title="Test Event",
            host=self.host,
            start_location=self.art,
            start_time=datetime.now() + timedelta(days=1),
        )
        self.itinerary = Itinerary.objects.create(user=self.user, title="Test Tour")

    def test_favorite_all_types(self):
        """Test favoriting all three types and viewing them"""
        UserFavoriteArt.objects.create(user=self.user, art=self.art)
        EventFavorite.objects.create(user=self.user, event=self.event)
        ItineraryFavorite.objects.create(user=self.user, itinerary=self.itinerary)

        self.client.login(username="testuser", password="testpass123")

        # Check art tab
        response = self.client.get(reverse("favorites:index") + "?tab=art")
        self.assertEqual(len(response.context["page_obj"]), 1)

        # Check events tab
        response = self.client.get(reverse("favorites:index") + "?tab=events")
        self.assertEqual(len(response.context["page_obj"]), 1)

        # Check itineraries tab
        response = self.client.get(reverse("favorites:index") + "?tab=itineraries")
        self.assertEqual(len(response.context["itineraries"]), 1)

    def test_unfavorite_from_unified_page(self):
        """Test unfavoriting from the unified favorites page"""
        EventFavorite.objects.create(user=self.user, event=self.event)

        self.client.login(username="testuser", password="testpass123")

        # Unfavorite the event
        response = self.client.post(
            reverse("events:unfavorite", args=[self.event.slug]),
            HTTP_REFERER=reverse("favorites:index") + "?tab=events",
        )
        self.assertEqual(response.status_code, 302)

        # Verify it's removed
        self.assertFalse(
            EventFavorite.objects.filter(user=self.user, event=self.event).exists()
        )

    def test_multiple_users_favorites_isolated(self):
        """Test that users only see their own favorites"""
        other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )

        # User 1 favorites
        UserFavoriteArt.objects.create(user=self.user, art=self.art)

        # User 2 favorites different items
        art2 = PublicArt.objects.create(
            title="Art 2",
            latitude=Decimal("40.7480"),
            longitude=Decimal("-73.8448"),
            external_id="art002",
        )
        UserFavoriteArt.objects.create(user=other_user, art=art2)

        # Login as user 1
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=art")
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 1)
        self.assertEqual(page_obj[0].art.title, "Test Art")

        # Login as user 2
        self.client.logout()
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.get(reverse("favorites:index") + "?tab=art")
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 1)
        self.assertEqual(page_obj[0].art.title, "Art 2")
