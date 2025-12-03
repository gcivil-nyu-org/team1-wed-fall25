"""
Tests for frontend image validation functionality
CORRECTED VERSION - Creates review before checking edit form
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from loc_detail.models import PublicArt, ArtComment  # Added ArtComment import


class ImageValidationFrontendTests(TestCase):
    """Test that image validation messages are present in the template"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
        )

    def test_art_detail_contains_image_size_limit_message(self):
        """Test that the art detail page shows image size limit"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id})
        )

        self.assertEqual(response.status_code, 200)
        # Check for 10MB reference and Max 5 images
        self.assertContains(response, "10")  # JavaScript has 10 * 1024 * 1024
        self.assertContains(response, "Max 5 images")

    def test_art_detail_contains_error_display_elements(self):
        """Test that error display elements are present"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="image-size-error"')
        self.assertContains(response, 'id="error-message"')

    def test_art_detail_contains_validation_javascript(self):
        """Test that validation JavaScript is included"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MAX_FILE_SIZE")
        self.assertContains(response, "validateImageSize")
        self.assertContains(response, "validateMultipleImages")

    def test_edit_form_contains_image_size_validation(self):
        """Test that edit form also has image size validation"""
        self.client.login(username="testuser", password="testpass123")

        # FIXED: Create a review first so the edit form appears
        # The edit form is only shown if the user has already posted a review
        ArtComment.objects.create(
            art=self.art,
            user=self.user,
            rating=5,
            comment="Test review for testing edit form",
        )

        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="edit-image-size-error"')
        self.assertContains(response, 'id="edit-error-message"')
