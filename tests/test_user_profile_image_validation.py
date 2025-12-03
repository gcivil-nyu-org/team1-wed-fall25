"""
Tests for image upload validation and unsaved changes warning
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import io
from PIL import Image


class ImageValidationTests(TestCase):
    """Test cases for profile image upload validation"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

    def create_test_image(self, size_mb=1, format="PNG"):
        """Helper to create test image of specified size"""
        # Create image in memory
        img = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        img.save(img_io, format=format)

        # Pad to desired size if needed
        current_size = img_io.tell()
        target_size = size_mb * 1024 * 1024
        if current_size < target_size:
            img_io.write(b"0" * (target_size - current_size))

        img_io.seek(0)
        return SimpleUploadedFile(
            name=f"test.{format.lower()}",
            content=img_io.read(),
            content_type=f"image/{format.lower()}",
        )

    def test_valid_image_size(self):
        """Test uploading image within size limit"""
        self.client.login(username="testuser", password="password123")

        # Create 1MB image (within 5MB limit)
        small_image = self.create_test_image(size_mb=1)

        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
                "about": "Test about",
                "privacy": "PUBLIC",
                "profile_image": small_image,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.profile.profile_image)

    def test_oversized_image_rejected(self):
        """Test that images over 5MB are rejected"""
        self.client.login(username="testuser", password="password123")

        # Create 6MB image (over 5MB limit)
        large_image = self.create_test_image(size_mb=6)

        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
                "about": "Test about",
                "privacy": "PUBLIC",
                "profile_image": large_image,
            },
        )

        # Should stay on edit page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Image file too large")

        # Image should not be saved
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile.profile_image)

    def test_different_image_formats(self):
        """Test uploading different image formats"""
        self.client.login(username="testuser", password="password123")

        formats = ["PNG", "JPEG"]

        for fmt in formats:
            image = self.create_test_image(size_mb=1, format=fmt)

            response = self.client.post(
                reverse("user_profile:edit_profile"),
                {
                    "username": "testuser",
                    "email": "test@example.com",
                    "full_name": "Test User",
                    "about": "Test about",
                    "privacy": "PUBLIC",
                    "profile_image": image,
                },
                follow=True,
            )

            self.assertEqual(response.status_code, 200)

    def test_edit_profile_page_has_image_input(self):
        """Test that edit profile page has image input with correct ID"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="profile-image-input"')
        self.assertContains(response, "Maximum file size: 5MB")

    def test_image_preview_container_exists(self):
        """Test that image preview elements exist in template"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="image-preview-container"')
        self.assertContains(response, 'id="image-preview"')
        self.assertContains(response, 'id="clear-preview"')

    def test_error_message_container_exists(self):
        """Test that error message container exists"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="image-size-error"')


class UnsavedChangesTests(TestCase):
    """Test cases for unsaved changes warning"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

    def test_cancel_button_has_id(self):
        """Test that cancel button has correct ID for JavaScript"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="cancel-btn"')

    def test_form_has_id(self):
        """Test that form has correct ID"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="profile-form"')

    def test_save_button_has_id(self):
        """Test that save button has correct ID"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="save-btn"')

    def test_javascript_change_tracking_present(self):
        """Test that JavaScript for change tracking is present"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "formChanged")
        self.assertContains(response, "unsaved changes")

    def test_beforeunload_warning_present(self):
        """Test that beforeunload warning is implemented"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "beforeunload")


class IntegrationTests(TestCase):
    """Integration tests for image validation and form changes"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

    def test_edit_profile_page_loads_with_all_elements(self):
        """Test that edit profile page loads with all required elements"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)

        # Check form elements
        self.assertContains(response, 'id="profile-form"')
        self.assertContains(response, 'id="save-btn"')
        self.assertContains(response, 'id="cancel-btn"')

        # Check image validation elements
        self.assertContains(response, 'id="profile-image-input"')
        self.assertContains(response, 'id="image-size-error"')
        self.assertContains(response, 'id="image-preview-container"')

        # Check JavaScript is present
        self.assertContains(response, "formChanged")
        self.assertContains(response, "MAX_FILE_SIZE")

    def test_form_submission_successful(self):
        """Test that form can still be submitted successfully"""
        self.client.login(username="testuser", password="password123")

        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Updated Name",
                "about": "Updated about",
                "privacy": "PUBLIC",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.full_name, "Updated Name")
