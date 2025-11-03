"""
Tests for the itineraries app
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import time
from .models import Itinerary, ItineraryStop
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

    def test_itinerary_get_absolute_url(self):
        """Test get_absolute_url method"""
        itinerary = Itinerary.objects.create(user=self.user, title="My Art Tour")
        url = itinerary.get_absolute_url()
        self.assertEqual(url, f"/itineraries/{itinerary.pk}/")


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

    def test_stop_creation(self):
        """Test creating a stop"""
        stop = ItineraryStop.objects.create(
            itinerary=self.itinerary,
            location=self.location,
            order=1,
            visit_time=time(10, 0),
        )
        self.assertEqual(stop.order, 1)
        self.assertEqual(str(stop), "My Art Tour - Stop 1: Test Art")


class ItineraryViewTests(TestCase):
    """Tests for itinerary views"""

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
