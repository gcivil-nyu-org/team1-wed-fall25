"""
Comprehensive test coverage for itineraries/views.py
Targets uncovered lines to boost coverage from 73.78% to 90%+
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from loc_detail.models import PublicArt
from itineraries.models import Itinerary, ItineraryStop, ItineraryFavorite
import json


class ItineraryCreateViewTests(TestCase):
    """Test itinerary creation with error handling"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

        self.location1 = PublicArt.objects.create(
            title="Art 1",
            latitude=40.7128,
            longitude=-74.0060,
        )
        self.location2 = PublicArt.objects.create(
            title="Art 2",
            latitude=40.7580,
            longitude=-73.9855,
        )

    def test_create_with_transaction_exception(self):
        """Test create view handling transaction exceptions (line 87-98)"""
        # Post invalid formset data to trigger exception
        response = self.client.post(
            reverse("itineraries:create"),
            {
                "title": "Test Itinerary",
                "description": "Test Description",
                "date": "2025-12-01",
                # Invalid formset data
                "stops-TOTAL_FORMS": "1",
                "stops-INITIAL_FORMS": "0",
                "stops-0-location": "999999",  # Non-existent location
                "stops-0-order": "1",
            },
        )

        # Should stay on create page with error message
        self.assertEqual(response.status_code, 200)

    def test_create_with_form_errors(self):
        """Test create view showing form errors (line 87-98)"""
        response = self.client.post(
            reverse("itineraries:create"),
            {
                "title": "",  # Empty title
                "description": "Test Description",
                "date": "2025-12-01",
                "stops-TOTAL_FORMS": "0",
                "stops-INITIAL_FORMS": "0",
            },
        )

        # Should stay on create page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "itineraries/create_improved.html")

    def test_create_with_formset_errors(self):
        """Test create view showing formset errors (line 87-98)"""
        response = self.client.post(
            reverse("itineraries:create"),
            {
                "title": "Test Itinerary",
                "description": "Test Description",
                "date": "2025-12-01",
                "stops-TOTAL_FORMS": "1",
                "stops-INITIAL_FORMS": "0",
                "stops-0-location": "",  # Empty location
                "stops-0-order": "",  # Empty order
            },
        )

        # Should stay on create page with formset errors
        self.assertEqual(response.status_code, 200)


class ItineraryEditViewTests(TestCase):
    """Test itinerary editing with error handling"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

        self.location = PublicArt.objects.create(
            title="Art Location",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.itinerary = Itinerary.objects.create(
            user=self.user,
            title="Test Itinerary",
            description="Test Description",
        )
        ItineraryStop.objects.create(
            itinerary=self.itinerary,
            location=self.location,
            order=1,
        )

    def test_edit_with_transaction_exception(self):
        """Test edit view handling transaction exceptions (line 136-147)"""
        response = self.client.post(
            reverse("itineraries:edit", kwargs={"pk": self.itinerary.pk}),
            {
                "title": "Updated Title",
                "description": "Updated Description",
                "date": "2025-12-01",
                # Invalid formset
                "stops-TOTAL_FORMS": "1",
                "stops-INITIAL_FORMS": "1",
                "stops-0-id": "999999",  # Non-existent stop ID
                "stops-0-location": self.location.id,
                "stops-0-order": "1",
            },
        )

        # Should stay on edit page
        self.assertEqual(response.status_code, 200)

    def test_edit_with_form_errors(self):
        """Test edit view showing form errors (line 136-147)"""
        response = self.client.post(
            reverse("itineraries:edit", kwargs={"pk": self.itinerary.pk}),
            {
                "title": "",  # Empty title
                "description": "Updated Description",
                "date": "2025-12-01",
                "stops-TOTAL_FORMS": "1",
                "stops-INITIAL_FORMS": "1",
                "stops-0-id": self.itinerary.stops.first().id,
                "stops-0-location": self.location.id,
                "stops-0-order": "1",
            },
        )

        # Should stay on edit page
        self.assertEqual(response.status_code, 200)

    def test_edit_with_formset_errors(self):
        """Test edit view showing formset errors (line 136-147)"""
        response = self.client.post(
            reverse("itineraries:edit", kwargs={"pk": self.itinerary.pk}),
            {
                "title": "Updated Title",
                "description": "Updated Description",
                "date": "2025-12-01",
                "stops-TOTAL_FORMS": "1",
                "stops-INITIAL_FORMS": "1",
                "stops-0-id": self.itinerary.stops.first().id,
                "stops-0-location": "",  # Empty location
                "stops-0-order": "",  # Empty order
            },
        )

        # Should stay on edit page with formset errors
        self.assertEqual(response.status_code, 200)


class ItineraryDeleteViewTests(TestCase):
    """Test itinerary deletion"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

        self.itinerary = Itinerary.objects.create(
            user=self.user,
            title="Test Itinerary",
            description="Test Description",
        )

    def test_delete_get_shows_confirm_page(self):
        """Test delete GET request shows confirmation page (line 178-181)"""
        response = self.client.get(
            reverse("itineraries:delete", kwargs={"pk": self.itinerary.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "itineraries/delete_confirm.html")
        self.assertEqual(response.context["itinerary"], self.itinerary)


class APISearchLocationsTests(TestCase):
    """Test location search API"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

        self.location = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
            borough="Manhattan",
            location="Central Park",
            latitude=40.7128,
            longitude=-74.0060,
        )

    def test_search_locations_short_query(self):
        """Test search with query < 2 chars (line 187-207)"""
        response = self.client.get(
            reverse("itineraries:api_search_locations"), {"q": "a"}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["results"], [])

    def test_search_locations_valid_query(self):
        """Test search with valid query"""
        response = self.client.get(
            reverse("itineraries:api_search_locations"), {"q": "Test"}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["title"], "Test Art")


class APIAddToItineraryTests(TestCase):
    """Test add to itinerary API"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

        self.location = PublicArt.objects.create(
            title="Test Art",
            latitude=40.7128,
            longitude=-74.0060,
        )

        self.itinerary = Itinerary.objects.create(
            user=self.user,
            title="Existing Itinerary",
        )

    def test_add_to_itinerary_no_itinerary_specified(self):
        """Test add to itinerary without specifying itinerary (line 253)"""
        response = self.client.post(
            reverse("itineraries:api_add_to_itinerary"),
            {
                "location_id": self.location.id,
                # No itinerary_id or new_itinerary_title
            },
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("No itinerary specified", data["error"])

    def test_add_to_itinerary_duplicate_location(self):
        """Test adding duplicate location to itinerary (line 302-303)"""
        # Add location first time
        ItineraryStop.objects.create(
            itinerary=self.itinerary,
            location=self.location,
            order=1,
        )

        # Try to add again
        response = self.client.post(
            reverse("itineraries:api_add_to_itinerary"),
            {
                "location_id": self.location.id,
                "itinerary_id": self.itinerary.id,
            },
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("already in", data["error"])

    def test_add_to_new_itinerary(self):
        """Test adding location to new itinerary"""
        response = self.client.post(
            reverse("itineraries:api_add_to_itinerary"),
            {
                "location_id": self.location.id,
                "new_itinerary_title": "New Itinerary",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Verify itinerary was created
        new_itinerary = Itinerary.objects.get(title="New Itinerary")
        self.assertEqual(new_itinerary.user, self.user)
        self.assertEqual(new_itinerary.stops.count(), 1)

    def test_add_to_existing_itinerary_with_stops(self):
        """Test adding location to existing itinerary with stops (line 326-327)"""
        # Add first stop
        ItineraryStop.objects.create(
            itinerary=self.itinerary,
            location=self.location,
            order=1,
        )

        # Create second location
        location2 = PublicArt.objects.create(
            title="Art 2",
            latitude=40.7580,
            longitude=-73.9855,
        )

        # Add second location
        response = self.client.post(
            reverse("itineraries:api_add_to_itinerary"),
            {
                "location_id": location2.id,
                "itinerary_id": self.itinerary.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Verify order is correct
        last_stop = self.itinerary.stops.order_by("-order").first()
        self.assertEqual(last_stop.order, 2)
        self.assertEqual(last_stop.location, location2)


class FavoriteItineraryViewTests(TestCase):
    """Test favorite/unfavorite functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.other_user = User.objects.create_user(
            username="otheruser", password="testpass"
        )
        self.client.login(username="testuser", password="testpass")

        self.itinerary = Itinerary.objects.create(
            user=self.other_user,
            title="Test Itinerary",
        )

    def test_favorite_itinerary_with_exception(self):
        """Test favorite with exception handling (line 336-357)"""
        # First favorite should succeed
        response = self.client.post(
            reverse("itineraries:favorite", kwargs={"pk": self.itinerary.pk})
        )

        self.assertEqual(response.status_code, 302)

        # Verify favorite was created
        self.assertTrue(
            ItineraryFavorite.objects.filter(
                itinerary=self.itinerary, user=self.user
            ).exists()
        )

    def test_unfavorite_not_favorited(self):
        """Test unfavorite when not in favorites (line 336-357)"""
        response = self.client.post(
            reverse("itineraries:unfavorite", kwargs={"pk": self.itinerary.pk})
        )

        self.assertEqual(response.status_code, 302)

    def test_unfavorite_success(self):
        """Test successful unfavorite"""
        # Create favorite first
        ItineraryFavorite.objects.create(
            itinerary=self.itinerary,
            user=self.user,
        )

        # Unfavorite
        response = self.client.post(
            reverse("itineraries:unfavorite", kwargs={"pk": self.itinerary.pk})
        )

        self.assertEqual(response.status_code, 302)

        # Verify favorite was deleted
        self.assertFalse(
            ItineraryFavorite.objects.filter(
                itinerary=self.itinerary, user=self.user
            ).exists()
        )


class EdgeCaseTests(TestCase):
    """Test edge cases and boundary conditions"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

    def test_create_get_request_loads_form(self):
        """Test create GET request loads empty form"""
        response = self.client.get(reverse("itineraries:create"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "itineraries/create_improved.html")
        self.assertIn("form", response.context)
        self.assertIn("formset", response.context)
        self.assertIn("locations", response.context)
        self.assertFalse(response.context["is_edit"])

    def test_edit_get_request_loads_form(self):
        """Test edit GET request loads form with data"""
        itinerary = Itinerary.objects.create(
            user=self.user,
            title="Test Itinerary",
        )

        response = self.client.get(
            reverse("itineraries:edit", kwargs={"pk": itinerary.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "itineraries/create_improved.html")
        self.assertTrue(response.context["is_edit"])

    def test_api_add_to_empty_itinerary(self):
        """Test adding first location to empty itinerary"""
        itinerary = Itinerary.objects.create(
            user=self.user,
            title="Empty Itinerary",
        )

        location = PublicArt.objects.create(
            title="Test Art",
            latitude=40.7128,
            longitude=-74.0060,
        )

        response = self.client.post(
            reverse("itineraries:api_add_to_itinerary"),
            {
                "location_id": location.id,
                "itinerary_id": itinerary.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Verify first stop has order 1
        stop = itinerary.stops.first()
        self.assertEqual(stop.order, 1)

    def test_search_locations_empty_query(self):
        """Test search with empty query"""
        response = self.client.get(
            reverse("itineraries:api_search_locations"), {"q": ""}
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["results"], [])

    def test_api_get_user_itineraries(self):
        """Test getting user's itineraries via API"""
        # Create multiple itineraries
        Itinerary.objects.create(user=self.user, title="Itinerary 1")
        Itinerary.objects.create(user=self.user, title="Itinerary 2")

        response = self.client.get(reverse("itineraries:api_user_itineraries"))

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data["itineraries"]), 2)

    def test_create_with_valid_data_and_stops(self):
        """Test successful creation with stops"""
        location = PublicArt.objects.create(
            title="Test Art",
            latitude=40.7128,
            longitude=-74.0060,
        )

        response = self.client.post(
            reverse("itineraries:create"),
            {
                "title": "New Itinerary",
                "description": "Description",
                "date": "2025-12-01",
                "stops-TOTAL_FORMS": "1",
                "stops-INITIAL_FORMS": "0",
                "stops-0-location": location.id,
                "stops-0-order": "1",
                "stops-0-visit_time": "",
                "stops-0-notes": "",
            },
        )

        # Should redirect to detail page
        self.assertEqual(response.status_code, 302)

        # Verify itinerary was created
        itinerary = Itinerary.objects.get(title="New Itinerary")
        self.assertEqual(itinerary.user, self.user)
        self.assertEqual(itinerary.stops.count(), 1)

    def test_edit_with_valid_data(self):
        """Test successful edit"""
        location = PublicArt.objects.create(
            title="Test Art",
            latitude=40.7128,
            longitude=-74.0060,
        )

        itinerary = Itinerary.objects.create(
            user=self.user,
            title="Original Title",
        )
        stop = ItineraryStop.objects.create(
            itinerary=itinerary,
            location=location,
            order=1,
        )

        response = self.client.post(
            reverse("itineraries:edit", kwargs={"pk": itinerary.pk}),
            {
                "title": "Updated Title",
                "description": "Updated Description",
                "date": "2025-12-01",
                "stops-TOTAL_FORMS": "1",
                "stops-INITIAL_FORMS": "1",
                "stops-0-id": stop.id,
                "stops-0-location": location.id,
                "stops-0-order": "1",
                "stops-0-visit_time": "",
                "stops-0-notes": "",
            },
        )

        # Should redirect to detail page
        self.assertEqual(response.status_code, 302)

        # Verify itinerary was updated
        itinerary.refresh_from_db()
        self.assertEqual(itinerary.title, "Updated Title")
