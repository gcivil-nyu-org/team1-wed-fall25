"""
Extended tests for the itineraries app
Tests for favorites, date field, forms validation, and edge cases
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import time, date
from itineraries.models import Itinerary, ItineraryStop, ItineraryFavorite
from itineraries.forms import ItineraryForm, ItineraryStopForm
from loc_detail.models import PublicArt


class ItineraryWithDateTests(TestCase):
    """Tests for itinerary date field functionality"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

    def test_create_itinerary_with_date(self):
        """Test creating an itinerary with a planned date"""
        itinerary = Itinerary.objects.create(
            user=self.user,
            title="Summer Art Tour",
            description="A great summer tour",
            date=date(2025, 7, 15),
        )
        self.assertEqual(itinerary.date, date(2025, 7, 15))
        self.assertEqual(itinerary.title, "Summer Art Tour")

    def test_create_itinerary_without_date(self):
        """Test creating an itinerary without a date"""
        itinerary = Itinerary.objects.create(
            user=self.user, title="Flexible Tour", description="No specific date"
        )
        self.assertIsNone(itinerary.date)

    def test_update_itinerary_date(self):
        """Test updating an itinerary's date"""
        itinerary = Itinerary.objects.create(user=self.user, title="Tour")
        self.assertIsNone(itinerary.date)

        itinerary.date = date(2025, 8, 1)
        itinerary.save()
        itinerary.refresh_from_db()
        self.assertEqual(itinerary.date, date(2025, 8, 1))

    def test_remove_itinerary_date(self):
        """Test removing a date from an itinerary"""
        itinerary = Itinerary.objects.create(
            user=self.user, title="Tour", date=date(2025, 7, 15)
        )
        itinerary.date = None
        itinerary.save()
        itinerary.refresh_from_db()
        self.assertIsNone(itinerary.date)


class ItineraryFormWithDateTests(TestCase):
    """Tests for ItineraryForm with date field"""

    def test_form_with_date(self):
        """Test form with date field"""
        form_data = {
            "title": "My Tour",
            "description": "Great tour",
            "date": "2025-07-15",
        }
        form = ItineraryForm(data=form_data)
        self.assertTrue(form.is_valid())
        itinerary = form.save(commit=False)
        self.assertEqual(itinerary.date, date(2025, 7, 15))

    def test_form_without_date(self):
        """Test form without date (optional field)"""
        form_data = {"title": "My Tour", "description": "Great tour"}
        form = ItineraryForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_date_widget(self):
        """Test that date field has correct widget attributes"""
        form = ItineraryForm()
        date_widget = form.fields["date"].widget
        # Widget type is set in widget declaration
        self.assertEqual(date_widget.attrs.get("class"), "form-control")

    def test_form_date_help_text(self):
        """Test that date field has help text"""
        form = ItineraryForm()
        self.assertIn("Planned date", form.fields["date"].help_text)


class ItineraryStopFormTests(TestCase):
    """Extended tests for ItineraryStopForm"""

    def setUp(self):
        self.location = PublicArt.objects.create(
            title="Test Art",
            latitude=Decimal("40.7580"),
            longitude=Decimal("-73.9855"),
            external_id="test001",
        )

    def test_form_with_notes(self):
        """Test form with notes field"""
        form_data = {
            "location": self.location.id,
            "order": 1,
            "visit_time": "10:00",
            "notes": "Visit early to avoid crowds",
        }
        form = ItineraryStopForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["notes"], "Visit early to avoid crowds")

    def test_form_without_notes(self):
        """Test form without notes (optional field)"""
        form_data = {
            "location": self.location.id,
            "order": 1,
            "visit_time": "10:00",
        }
        form = ItineraryStopForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_notes_widget(self):
        """Test that notes field has correct widget"""
        form = ItineraryStopForm()
        notes_widget = form.fields["notes"].widget
        self.assertEqual(notes_widget.attrs.get("rows"), "2")
        self.assertEqual(notes_widget.attrs.get("class"), "form-control")

    def test_form_order_min_value(self):
        """Test that order field has minimum value"""
        form = ItineraryStopForm()
        order_widget = form.fields["order"].widget
        # Min value is 0 or 1 depending on form configuration
        self.assertIsNotNone(order_widget.attrs.get("min"))

    def test_form_visit_time_not_required(self):
        """Test that visit_time is not required"""
        form_data = {
            "location": self.location.id,
            "order": 1,
        }
        form = ItineraryStopForm(data=form_data)
        self.assertTrue(form.is_valid())


class ItineraryFavoriteModelTests(TestCase):
    """Tests for ItineraryFavorite model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        self.itinerary = Itinerary.objects.create(user=self.user, title="My Art Tour")

    def test_favorite_creation(self):
        """Test creating a favorite"""
        favorite = ItineraryFavorite.objects.create(
            itinerary=self.itinerary, user=self.user
        )
        self.assertEqual(
            str(favorite), f"{self.user.username} favorited {self.itinerary.title}"
        )
        self.assertEqual(favorite.itinerary, self.itinerary)
        self.assertEqual(favorite.user, self.user)

    def test_favorite_has_timestamp(self):
        """Test that favorite has created_at timestamp"""
        favorite = ItineraryFavorite.objects.create(
            itinerary=self.itinerary, user=self.user
        )
        self.assertIsNotNone(favorite.created_at)

    def test_favorite_unique_constraint(self):
        """Test that user can't favorite same itinerary twice"""
        ItineraryFavorite.objects.create(itinerary=self.itinerary, user=self.user)

        # Try to create duplicate - should use get_or_create in practice
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            ItineraryFavorite.objects.create(itinerary=self.itinerary, user=self.user)

    def test_multiple_users_can_favorite_same_itinerary(self):
        """Test that multiple users can favorite the same itinerary"""
        ItineraryFavorite.objects.create(itinerary=self.itinerary, user=self.user)
        ItineraryFavorite.objects.create(itinerary=self.itinerary, user=self.other_user)
        self.assertEqual(ItineraryFavorite.objects.count(), 2)

    def test_user_can_favorite_multiple_itineraries(self):
        """Test that user can favorite multiple itineraries"""
        itinerary2 = Itinerary.objects.create(user=self.user, title="Second Tour")
        ItineraryFavorite.objects.create(itinerary=self.itinerary, user=self.user)
        ItineraryFavorite.objects.create(itinerary=itinerary2, user=self.user)
        self.assertEqual(ItineraryFavorite.objects.filter(user=self.user).count(), 2)

    def test_favorite_ordering(self):
        """Test that favorites are ordered by created_at descending"""
        from time import sleep

        fav1 = ItineraryFavorite.objects.create(
            itinerary=self.itinerary, user=self.user
        )
        sleep(0.01)
        itinerary2 = Itinerary.objects.create(user=self.user, title="Second Tour")
        fav2 = ItineraryFavorite.objects.create(itinerary=itinerary2, user=self.user)

        favorites = list(ItineraryFavorite.objects.all())
        self.assertEqual(favorites[0], fav2)  # Most recent first
        self.assertEqual(favorites[1], fav1)

    def test_favorite_cascade_on_itinerary_delete(self):
        """Test that favorites are deleted when itinerary is deleted"""
        ItineraryFavorite.objects.create(itinerary=self.itinerary, user=self.user)
        self.assertEqual(ItineraryFavorite.objects.count(), 1)

        self.itinerary.delete()
        self.assertEqual(ItineraryFavorite.objects.count(), 0)

    def test_favorite_cascade_on_user_delete(self):
        """Test that favorites are deleted when user is deleted"""
        ItineraryFavorite.objects.create(itinerary=self.itinerary, user=self.user)
        self.assertEqual(ItineraryFavorite.objects.count(), 1)

        self.user.delete()
        self.assertEqual(ItineraryFavorite.objects.count(), 0)


class ItineraryFavoriteViewTests(TestCase):
    """Tests for itinerary favorite views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", password="testpass123"
        )
        self.itinerary = Itinerary.objects.create(user=self.user, title="My Art Tour")

    def test_favorite_requires_login(self):
        """Test that favorite view requires login"""
        response = self.client.post(
            reverse("itineraries:favorite", args=[self.itinerary.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_favorite_requires_post(self):
        """Test that favorite view requires POST"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("itineraries:favorite", args=[self.itinerary.pk])
        )
        self.assertEqual(response.status_code, 405)

    def test_add_to_favorites(self):
        """Test adding itinerary to favorites"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("itineraries:favorite", args=[self.itinerary.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ItineraryFavorite.objects.filter(
                itinerary=self.itinerary, user=self.user
            ).exists()
        )

    def test_favorite_idempotent(self):
        """Test that favoriting twice doesn't create duplicates"""
        self.client.login(username="testuser", password="testpass123")
        self.client.post(reverse("itineraries:favorite", args=[self.itinerary.pk]))
        self.client.post(reverse("itineraries:favorite", args=[self.itinerary.pk]))
        self.assertEqual(
            ItineraryFavorite.objects.filter(
                itinerary=self.itinerary, user=self.user
            ).count(),
            1,
        )

    def test_favorite_own_itinerary(self):
        """Test that user can favorite their own itinerary"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("itineraries:favorite", args=[self.itinerary.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ItineraryFavorite.objects.filter(
                itinerary=self.itinerary, user=self.user
            ).exists()
        )

    def test_favorite_other_user_itinerary(self):
        """Test that user can favorite another user's itinerary"""
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.post(
            reverse("itineraries:favorite", args=[self.itinerary.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ItineraryFavorite.objects.filter(
                itinerary=self.itinerary, user=self.other_user
            ).exists()
        )

    def test_favorite_nonexistent_itinerary(self):
        """Test favoriting a non-existent itinerary returns 404"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("itineraries:favorite", args=[99999]))
        self.assertEqual(response.status_code, 404)


class ItineraryUnfavoriteViewTests(TestCase):
    """Tests for itinerary unfavorite views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.itinerary = Itinerary.objects.create(user=self.user, title="My Art Tour")

    def test_unfavorite_requires_login(self):
        """Test that unfavorite view requires login"""
        response = self.client.post(
            reverse("itineraries:unfavorite", args=[self.itinerary.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_unfavorite_requires_post(self):
        """Test that unfavorite view requires POST"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("itineraries:unfavorite", args=[self.itinerary.pk])
        )
        self.assertEqual(response.status_code, 405)

    def test_remove_from_favorites(self):
        """Test removing itinerary from favorites"""
        ItineraryFavorite.objects.create(itinerary=self.itinerary, user=self.user)
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("itineraries:unfavorite", args=[self.itinerary.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ItineraryFavorite.objects.filter(
                itinerary=self.itinerary, user=self.user
            ).exists()
        )

    def test_unfavorite_not_favorited(self):
        """Test unfavoriting an itinerary that wasn't favorited"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("itineraries:unfavorite", args=[self.itinerary.pk])
        )
        self.assertEqual(response.status_code, 302)
        # Should not raise error, just show info message

    def test_unfavorite_nonexistent_itinerary(self):
        """Test unfavoriting a non-existent itinerary returns 404"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("itineraries:unfavorite", args=[99999]))
        self.assertEqual(response.status_code, 404)


class ItineraryListViewWithFavoritesTests(TestCase):
    """Tests for list view showing favorite status"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.itinerary1 = Itinerary.objects.create(user=self.user, title="Tour 1")
        self.itinerary2 = Itinerary.objects.create(user=self.user, title="Tour 2")

    def test_list_shows_favorite_status(self):
        """Test that list view marks favorited itineraries"""
        ItineraryFavorite.objects.create(itinerary=self.itinerary1, user=self.user)
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("itineraries:list"))
        itineraries = response.context["itineraries"]

        # Find the itineraries in the response
        itin1 = next((i for i in itineraries if i.id == self.itinerary1.id), None)
        itin2 = next((i for i in itineraries if i.id == self.itinerary2.id), None)

        self.assertTrue(itin1.is_favorited)
        self.assertFalse(itin2.is_favorited)


class ItineraryDetailViewWithFavoritesTests(TestCase):
    """Tests for detail view showing favorite status"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.itinerary = Itinerary.objects.create(user=self.user, title="My Art Tour")

    def test_detail_shows_favorite_status_false(self):
        """Test that detail view shows not favorited"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("itineraries:detail", args=[self.itinerary.pk])
        )
        self.assertFalse(response.context["is_favorited"])

    def test_detail_shows_favorite_status_true(self):
        """Test that detail view shows favorited"""
        ItineraryFavorite.objects.create(itinerary=self.itinerary, user=self.user)
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("itineraries:detail", args=[self.itinerary.pk])
        )
        self.assertTrue(response.context["is_favorited"])


class ItineraryEdgeCaseTests(TestCase):
    """Tests for edge cases and error handling"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Test Art",
            latitude=Decimal("40.7580"),
            longitude=Decimal("-73.9855"),
            external_id="test001",
        )

    def test_itinerary_with_very_long_title(self):
        """Test itinerary with maximum length title"""
        long_title = "A" * 200
        itinerary = Itinerary.objects.create(user=self.user, title=long_title)
        self.assertEqual(len(itinerary.title), 200)

    def test_itinerary_with_special_characters(self):
        """Test itinerary with special characters in title"""
        special_title = "Art Tour: NYC's Best! @2025 #Amazing"
        itinerary = Itinerary.objects.create(user=self.user, title=special_title)
        self.assertEqual(itinerary.title, special_title)

    def test_stop_with_midnight_time(self):
        """Test stop with midnight visit time"""
        itinerary = Itinerary.objects.create(user=self.user, title="Night Tour")
        stop = ItineraryStop.objects.create(
            itinerary=itinerary,
            location=self.location,
            order=1,
            visit_time=time(0, 0),
        )
        self.assertEqual(stop.visit_time, time(0, 0))

    def test_stop_with_late_night_time(self):
        """Test stop with late night visit time"""
        itinerary = Itinerary.objects.create(user=self.user, title="Night Tour")
        stop = ItineraryStop.objects.create(
            itinerary=itinerary,
            location=self.location,
            order=1,
            visit_time=time(23, 59),
        )
        self.assertEqual(stop.visit_time, time(23, 59))

    def test_itinerary_with_many_stops(self):
        """Test itinerary with many stops"""
        itinerary = Itinerary.objects.create(user=self.user, title="Marathon Tour")

        # Create multiple locations
        locations = []
        for i in range(20):
            loc = PublicArt.objects.create(
                title=f"Art {i}",
                latitude=Decimal("40.7580") + Decimal(str(i * 0.01)),
                longitude=Decimal("-73.9855") + Decimal(str(i * 0.01)),
                external_id=f"art{i:03d}",
            )
            locations.append(loc)
            ItineraryStop.objects.create(itinerary=itinerary, location=loc, order=i + 1)

        self.assertEqual(itinerary.stops.count(), 20)
        stops = list(itinerary.stops.all())
        self.assertEqual(stops[0].order, 1)
        self.assertEqual(stops[-1].order, 20)

    def test_delete_itinerary_with_favorites(self):
        """Test deleting itinerary that has favorites"""
        itinerary = Itinerary.objects.create(user=self.user, title="To Delete")
        ItineraryFavorite.objects.create(itinerary=itinerary, user=self.user)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("itineraries:delete", args=[itinerary.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Itinerary.objects.filter(pk=itinerary.pk).exists())
        # Favorites should also be deleted due to CASCADE
        self.assertFalse(
            ItineraryFavorite.objects.filter(itinerary_id=itinerary.pk).exists()
        )
