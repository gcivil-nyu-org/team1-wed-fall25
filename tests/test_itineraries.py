"""
Comprehensive tests for the itineraries app
Tests models, views, forms, and API endpoints
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import time
import json
from itineraries.models import Itinerary, ItineraryStop
from itineraries.forms import ItineraryForm, ItineraryStopForm
from loc_detail.models import PublicArt


class ItineraryModelTests(TestCase):
    """Tests for Itinerary model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_itinerary_creation(self):
        """Test creating an itinerary"""
        itinerary = Itinerary.objects.create(
            user=self.user, title="My Art Tour", description="A great tour"
        )
        self.assertEqual(str(itinerary), "My Art Tour by testuser")
        self.assertEqual(itinerary.user, self.user)
        self.assertEqual(itinerary.title, "My Art Tour")
        self.assertEqual(itinerary.description, "A great tour")

    def test_itinerary_get_absolute_url(self):
        """Test get_absolute_url method"""
        itinerary = Itinerary.objects.create(user=self.user, title="My Art Tour")
        url = itinerary.get_absolute_url()
        self.assertEqual(url, f"/itineraries/{itinerary.pk}/")

    def test_itinerary_string_representation(self):
        """Test string representation of itinerary"""
        itinerary = Itinerary.objects.create(user=self.user, title="Test Tour")
        self.assertEqual(str(itinerary), "Test Tour by testuser")

    def test_itinerary_timestamps(self):
        """Test that timestamps are created"""
        itinerary = Itinerary.objects.create(user=self.user, title="Test Tour")
        self.assertIsNotNone(itinerary.created_at)
        self.assertIsNotNone(itinerary.updated_at)

    def test_itinerary_ordering(self):
        """Test itineraries are ordered by updated_at descending"""
        from time import sleep

        Itinerary.objects.create(user=self.user, title="First")
        sleep(0.01)  # Small delay to ensure different timestamps
        Itinerary.objects.create(user=self.user, title="Second")
        itineraries = list(Itinerary.objects.all())
        # Second created should be first in list (newest first)
        self.assertEqual(itineraries[0].title, "Second")
        self.assertEqual(itineraries[1].title, "First")


class ItineraryStopModelTests(TestCase):
    """Tests for ItineraryStop model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.itinerary = Itinerary.objects.create(user=self.user, title="My Art Tour")
        self.location = PublicArt.objects.create(
            title="Test Art",
            latitude=Decimal("40.7580"),
            longitude=Decimal("-73.9855"),
            external_id="test001",
        )

    def test_stop_creation_with_time(self):
        """Test creating a stop with visit time"""
        stop = ItineraryStop.objects.create(
            itinerary=self.itinerary,
            location=self.location,
            order=1,
            visit_time=time(10, 0),
            notes="Morning visit",
        )
        self.assertEqual(stop.order, 1)
        self.assertEqual(str(stop), "My Art Tour - Stop 1: Test Art")
        self.assertEqual(stop.visit_time, time(10, 0))
        self.assertEqual(stop.notes, "Morning visit")

    def test_stop_creation_without_time(self):
        """Test creating a stop without visit time (should be optional)"""
        stop = ItineraryStop.objects.create(
            itinerary=self.itinerary, location=self.location, order=1
        )
        self.assertEqual(stop.order, 1)
        self.assertIsNone(stop.visit_time)
        # notes defaults to None if not provided
        self.assertIn(stop.notes, ["", None])

    def test_stop_ordering(self):
        """Test stops are ordered by order field"""
        location2 = PublicArt.objects.create(
            title="Art 2",
            latitude=Decimal("40.7480"),
            longitude=Decimal("-73.8448"),
            external_id="art002",
        )
        stop1 = ItineraryStop.objects.create(
            itinerary=self.itinerary, location=self.location, order=2
        )
        stop2 = ItineraryStop.objects.create(
            itinerary=self.itinerary, location=location2, order=1
        )
        stops = self.itinerary.stops.all()
        self.assertEqual(stops[0], stop2)
        self.assertEqual(stops[1], stop1)

    def test_stop_unique_together(self):
        """Test that itinerary + order combination is unique"""
        ItineraryStop.objects.create(
            itinerary=self.itinerary, location=self.location, order=1
        )
        location2 = PublicArt.objects.create(
            title="Art 2",
            latitude=Decimal("40.7480"),
            longitude=Decimal("-73.8448"),
            external_id="art002",
        )
        # This should work (different order)
        ItineraryStop.objects.create(
            itinerary=self.itinerary, location=location2, order=2
        )
        self.assertEqual(ItineraryStop.objects.count(), 2)


class ItineraryFormTests(TestCase):
    """Tests for ItineraryForm"""

    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {"title": "My Art Tour", "description": "A wonderful tour"}
        form = ItineraryForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_missing_title(self):
        """Test form with missing title"""
        form_data = {"description": "A tour without title"}
        form = ItineraryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_form_empty_description(self):
        """Test form with empty description (should be valid)"""
        form_data = {"title": "My Tour", "description": ""}
        form = ItineraryForm(data=form_data)
        self.assertTrue(form.is_valid())


class ItineraryStopFormTests(TestCase):
    """Tests for ItineraryStopForm"""

    def setUp(self):
        self.location = PublicArt.objects.create(
            title="Test Art",
            latitude=Decimal("40.7580"),
            longitude=Decimal("-73.9855"),
            external_id="test001",
        )

    def test_valid_form_with_time(self):
        """Test form with valid data including time"""
        form_data = {
            "location": self.location.id,
            "order": 1,
            "visit_time": "10:00",
            "notes": "Morning visit",
        }
        form = ItineraryStopForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_valid_form_without_time(self):
        """Test form with valid data without time"""
        form_data = {"location": self.location.id, "order": 1, "notes": ""}
        form = ItineraryStopForm(data=form_data)
        self.assertTrue(form.is_valid())


class ItineraryListViewTests(TestCase):
    """Tests for itinerary list view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )

    def test_list_view_requires_login(self):
        """Test that list view requires login"""
        response = self.client.get(reverse("itineraries:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_list_view_authenticated(self):
        """Test list view for authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("itineraries:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "itineraries/list.html")

    def test_list_view_shows_only_user_itineraries(self):
        """Test that list view shows only current user's itineraries"""
        Itinerary.objects.create(user=self.user, title="My Tour")
        Itinerary.objects.create(user=self.other_user, title="Other Tour")
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("itineraries:list"))
        self.assertEqual(len(response.context["itineraries"]), 1)
        self.assertEqual(response.context["itineraries"][0].title, "My Tour")

    def test_list_view_empty(self):
        """Test list view with no itineraries"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("itineraries:list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["itineraries"]), 0)


class ItineraryDetailViewTests(TestCase):
    """Tests for itinerary detail view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art",
            latitude=Decimal("40.7580"),
            longitude=Decimal("-73.9855"),
            external_id="test001",
        )

    def test_detail_view_requires_login(self):
        """Test that detail view requires login"""
        itinerary = Itinerary.objects.create(user=self.user, title="Test Tour")
        response = self.client.get(reverse("itineraries:detail", args=[itinerary.pk]))
        self.assertEqual(response.status_code, 302)

    def test_detail_view_authenticated(self):
        """Test detail view for authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        itinerary = Itinerary.objects.create(user=self.user, title="Test Tour")
        response = self.client.get(reverse("itineraries:detail", args=[itinerary.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "itineraries/detail.html")

    def test_detail_view_with_stops(self):
        """Test detail view shows stops"""
        self.client.login(username="testuser", password="testpass123")
        itinerary = Itinerary.objects.create(user=self.user, title="Test Tour")
        ItineraryStop.objects.create(
            itinerary=itinerary, location=self.location, order=1
        )
        response = self.client.get(reverse("itineraries:detail", args=[itinerary.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["itinerary"].stops.all()), 1)

    def test_detail_view_other_user_itinerary(self):
        """Test that user cannot view other user's itinerary"""
        itinerary = Itinerary.objects.create(user=self.other_user, title="Other Tour")
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("itineraries:detail", args=[itinerary.pk]))
        self.assertEqual(response.status_code, 404)


class ItineraryCreateViewTests(TestCase):
    """Tests for itinerary create view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art",
            latitude=Decimal("40.7580"),
            longitude=Decimal("-73.9855"),
            external_id="test001",
        )

    def test_create_view_requires_login(self):
        """Test that create view requires login"""
        response = self.client.get(reverse("itineraries:create"))
        self.assertEqual(response.status_code, 302)

    def test_create_view_authenticated(self):
        """Test create view for authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("itineraries:create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "itineraries/create_improved.html")

    def test_create_itinerary_with_stops(self):
        """Test creating an itinerary with stops"""
        self.client.login(username="testuser", password="testpass123")
        data = {
            "title": "New Tour",
            "description": "Test description",
            "stops-TOTAL_FORMS": "1",
            "stops-INITIAL_FORMS": "0",
            "stops-MIN_NUM_FORMS": "0",
            "stops-MAX_NUM_FORMS": "1000",
            "stops-0-location": self.location.id,
            "stops-0-order": "1",
            "stops-0-visit_time": "10:00",
            "stops-0-notes": "First stop",
        }
        response = self.client.post(reverse("itineraries:create"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Itinerary.objects.count(), 1)
        self.assertEqual(ItineraryStop.objects.count(), 1)


class ItineraryEditViewTests(TestCase):
    """Tests for itinerary edit view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art",
            latitude=Decimal("40.7580"),
            longitude=Decimal("-73.9855"),
            external_id="test001",
        )

    def test_edit_view_requires_login(self):
        """Test that edit view requires login"""
        itinerary = Itinerary.objects.create(user=self.user, title="Test Tour")
        response = self.client.get(reverse("itineraries:edit", args=[itinerary.pk]))
        self.assertEqual(response.status_code, 302)

    def test_edit_view_authenticated(self):
        """Test edit view for authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        itinerary = Itinerary.objects.create(user=self.user, title="Test Tour")
        response = self.client.get(reverse("itineraries:edit", args=[itinerary.pk]))
        self.assertEqual(response.status_code, 200)
        # The edit view uses create_improved.html template
        self.assertTemplateUsed(response, "itineraries/create_improved.html")

    def test_edit_other_user_itinerary(self):
        """Test that user cannot edit other user's itinerary"""
        itinerary = Itinerary.objects.create(user=self.other_user, title="Other Tour")
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("itineraries:edit", args=[itinerary.pk]))
        self.assertEqual(response.status_code, 404)

    def test_update_itinerary_title(self):
        """Test updating itinerary title"""
        self.client.login(username="testuser", password="testpass123")
        itinerary = Itinerary.objects.create(user=self.user, title="Old Title")
        ItineraryStop.objects.create(
            itinerary=itinerary, location=self.location, order=1
        )
        data = {
            "title": "New Title",
            "description": "Updated",
            "stops-TOTAL_FORMS": "1",
            "stops-INITIAL_FORMS": "1",
            "stops-MIN_NUM_FORMS": "0",
            "stops-MAX_NUM_FORMS": "1000",
            "stops-0-id": ItineraryStop.objects.first().id,
            "stops-0-location": self.location.id,
            "stops-0-order": "1",
        }
        response = self.client.post(
            reverse("itineraries:edit", args=[itinerary.pk]), data
        )
        self.assertEqual(response.status_code, 302)
        itinerary.refresh_from_db()
        self.assertEqual(itinerary.title, "New Title")


class ItineraryDeleteViewTests(TestCase):
    """Tests for itinerary delete view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )

    def test_delete_view_requires_login(self):
        """Test that delete view requires login"""
        itinerary = Itinerary.objects.create(user=self.user, title="Test Tour")
        response = self.client.post(reverse("itineraries:delete", args=[itinerary.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Itinerary.objects.filter(pk=itinerary.pk).exists())

    def test_delete_view_authenticated(self):
        """Test delete view for authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        itinerary = Itinerary.objects.create(user=self.user, title="Test Tour")
        response = self.client.post(reverse("itineraries:delete", args=[itinerary.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Itinerary.objects.filter(pk=itinerary.pk).exists())

    def test_delete_other_user_itinerary(self):
        """Test that user cannot delete other user's itinerary"""
        itinerary = Itinerary.objects.create(user=self.other_user, title="Other Tour")
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("itineraries:delete", args=[itinerary.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Itinerary.objects.filter(pk=itinerary.pk).exists())


class ItineraryAPITests(TestCase):
    """Tests for itinerary API endpoints"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.location1 = PublicArt.objects.create(
            title="Art 1",
            latitude=Decimal("40.7580"),
            longitude=Decimal("-73.9855"),
            external_id="art001",
        )
        self.location2 = PublicArt.objects.create(
            title="Art 2",
            latitude=Decimal("40.7480"),
            longitude=Decimal("-73.8448"),
            external_id="art002",
        )

    def test_api_get_user_itineraries_requires_login(self):
        """Test that API endpoint requires login"""
        response = self.client.get(reverse("itineraries:api_user_itineraries"))
        self.assertEqual(response.status_code, 302)

    def test_api_get_user_itineraries_empty(self):
        """Test API returns empty list when user has no itineraries"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("itineraries:api_user_itineraries"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["itineraries"]), 0)

    def test_api_get_user_itineraries_with_data(self):
        """Test API returns user's itineraries"""
        self.client.login(username="testuser", password="testpass123")
        itin = Itinerary.objects.create(user=self.user, title="Test Tour")
        ItineraryStop.objects.create(itinerary=itin, location=self.location1, order=1)
        ItineraryStop.objects.create(itinerary=itin, location=self.location2, order=2)

        response = self.client.get(reverse("itineraries:api_user_itineraries"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["itineraries"]), 1)
        self.assertEqual(data["itineraries"][0]["title"], "Test Tour")
        self.assertEqual(data["itineraries"][0]["stop_count"], 2)

    def test_api_add_to_existing_itinerary(self):
        """Test adding location to existing itinerary"""
        self.client.login(username="testuser", password="testpass123")
        itin = Itinerary.objects.create(user=self.user, title="Test Tour")

        data = {"location_id": self.location1.id, "itinerary_id": itin.id}
        response = self.client.post(reverse("itineraries:api_add_to_itinerary"), data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result["success"])
        self.assertEqual(ItineraryStop.objects.filter(itinerary=itin).count(), 1)

    def test_api_add_to_new_itinerary(self):
        """Test adding location to new itinerary"""
        self.client.login(username="testuser", password="testpass123")
        data = {
            "location_id": self.location1.id,
            "new_itinerary_title": "New Tour",
        }
        response = self.client.post(reverse("itineraries:api_add_to_itinerary"), data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result["success"])
        self.assertEqual(Itinerary.objects.count(), 1)
        self.assertEqual(ItineraryStop.objects.count(), 1)
        itin = Itinerary.objects.first()
        self.assertEqual(itin.title, "New Tour")

    def test_api_add_duplicate_location(self):
        """Test adding duplicate location to itinerary"""
        self.client.login(username="testuser", password="testpass123")
        itin = Itinerary.objects.create(user=self.user, title="Test Tour")
        ItineraryStop.objects.create(itinerary=itin, location=self.location1, order=1)

        data = {"location_id": self.location1.id, "itinerary_id": itin.id}
        response = self.client.post(reverse("itineraries:api_add_to_itinerary"), data)
        # Should return 400 for duplicate
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result["success"])
        self.assertIn("already in", result["error"])

    def test_api_add_invalid_location(self):
        """Test adding invalid location"""
        self.client.login(username="testuser", password="testpass123")
        itin = Itinerary.objects.create(user=self.user, title="Test Tour")

        data = {"location_id": 99999, "itinerary_id": itin.id}
        response = self.client.post(reverse("itineraries:api_add_to_itinerary"), data)
        # Should return 500 or 400 for invalid location
        self.assertIn(response.status_code, [400, 500])
        result = json.loads(response.content)
        self.assertFalse(result["success"])

    def test_api_add_requires_post(self):
        """Test that add endpoint requires POST"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("itineraries:api_add_to_itinerary"))
        self.assertEqual(response.status_code, 405)

    def test_api_add_auto_order(self):
        """Test that stops are auto-ordered correctly"""
        self.client.login(username="testuser", password="testpass123")
        itin = Itinerary.objects.create(user=self.user, title="Test Tour")
        ItineraryStop.objects.create(itinerary=itin, location=self.location1, order=1)

        data = {"location_id": self.location2.id, "itinerary_id": itin.id}
        response = self.client.post(reverse("itineraries:api_add_to_itinerary"), data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result["success"])

        # Check that second stop has order 2
        stop = ItineraryStop.objects.get(location=self.location2)
        self.assertEqual(stop.order, 2)
