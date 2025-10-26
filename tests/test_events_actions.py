"""
Test cases for event update, delete, and leave functionality
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from events.models import Event, EventMembership
from events.enums import EventVisibility, MembershipRole
from loc_detail.models import PublicArt


class EventUpdateDeleteLeaveTests(TestCase):
    """Test cases for update, delete, and leave event functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create users
        self.host = User.objects.create_user(
            username="host", email="host@test.com", password="testpass123"
        )
        self.attendee = User.objects.create_user(
            username="attendee", email="attendee@test.com", password="testpass123"
        )
        self.visitor = User.objects.create_user(
            username="visitor", email="visitor@test.com", password="testpass123"
        )

        # Create art location
        self.location = PublicArt.objects.create(
            title="Test Art", latitude=40.7128, longitude=-74.0060
        )

        # Create event
        self.event = Event.objects.create(
            title="Test Event",
            host=self.host,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
            description="Test Description",
        )

        # Create host membership
        EventMembership.objects.create(
            event=self.event, user=self.host, role=MembershipRole.HOST
        )

        # Create attendee membership
        EventMembership.objects.create(
            event=self.event, user=self.attendee, role=MembershipRole.ATTENDEE
        )

    def test_host_can_access_update_page(self):
        """Test that host can access the update page"""
        self.client.login(username="host", password="testpass123")
        response = self.client.get(
            reverse("events:update", kwargs={"slug": self.event.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Event")

    def test_non_host_cannot_access_update_page(self):
        """Test that non-host cannot access the update page"""
        self.client.login(username="attendee", password="testpass123")
        response = self.client.get(
            reverse("events:update", kwargs={"slug": self.event.slug})
        )
        self.assertEqual(response.status_code, 302)  # Redirected

    def test_host_can_delete_event(self):
        """Test that host can delete an event"""
        self.client.login(username="host", password="testpass123")
        response = self.client.post(
            reverse("events:delete", kwargs={"slug": self.event.slug})
        )

        # Should redirect to public events
        self.assertEqual(response.status_code, 302)

        # Event should be marked as deleted
        self.event.refresh_from_db()
        self.assertTrue(self.event.is_deleted)

    def test_non_host_cannot_delete_event(self):
        """Test that non-host cannot delete an event"""
        self.client.login(username="attendee", password="testpass123")
        response = self.client.post(
            reverse("events:delete", kwargs={"slug": self.event.slug})
        )

        # Should redirect back
        self.assertEqual(response.status_code, 302)

        # Event should NOT be deleted
        self.event.refresh_from_db()
        self.assertFalse(self.event.is_deleted)

    def test_attendee_can_leave_event(self):
        """Test that attendee can leave an event"""
        self.client.login(username="attendee", password="testpass123")

        # Verify attendee is registered
        self.assertTrue(
            EventMembership.objects.filter(
                event=self.event, user=self.attendee, role=MembershipRole.ATTENDEE
            ).exists()
        )

        response = self.client.post(
            reverse("events:leave", kwargs={"slug": self.event.slug})
        )

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Membership should be removed
        self.assertFalse(
            EventMembership.objects.filter(
                event=self.event, user=self.attendee, role=MembershipRole.ATTENDEE
            ).exists()
        )

    def test_host_cannot_leave_own_event(self):
        """Test that host cannot leave their own event"""
        self.client.login(username="host", password="testpass123")
        self.client.post(reverse("events:leave", kwargs={"slug": self.event.slug}))

        # Host membership should still exist
        self.assertTrue(
            EventMembership.objects.filter(
                event=self.event, user=self.host, role=MembershipRole.HOST
            ).exists()
        )

    def test_visitor_cannot_leave_event(self):
        """Test that visitor cannot leave an event they're not in"""
        self.client.login(username="visitor", password="testpass123")
        response = self.client.post(
            reverse("events:leave", kwargs={"slug": self.event.slug})
        )

        # Should handle gracefully (redirect)
        self.assertEqual(response.status_code, 302)

    def test_delete_requires_post(self):
        """Test that delete requires POST method"""
        self.client.login(username="host", password="testpass123")
        response = self.client.get(
            reverse("events:delete", kwargs={"slug": self.event.slug})
        )

        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)

    def test_leave_requires_post(self):
        """Test that leave requires POST method"""
        self.client.login(username="attendee", password="testpass123")
        response = self.client.get(
            reverse("events:leave", kwargs={"slug": self.event.slug})
        )

        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)
