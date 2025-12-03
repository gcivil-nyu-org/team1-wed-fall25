"""
Tests for image removal as pending action
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import io
from PIL import Image


class ImageRemovalPendingTests(TestCase):
    """Test that image removal is pending until save"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

        # Create a test image
        img = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)

        test_image = SimpleUploadedFile(
            name="test.png", content=img_io.read(), content_type="image/png"
        )

        # Set profile image
        self.user.profile.profile_image = test_image
        self.user.profile.save()

    def test_image_removal_with_form_submission(self):
        """Test that image is removed when remove_image=true is submitted"""
        self.client.login(username="testuser", password="password123")

        # Verify image exists
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile.profile_image)

        # Submit form with remove_image=true
        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
                "about": "Test",
                "privacy": "PUBLIC",
                "remove_image": "true",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        # FIXED: Changed from "image has been removed" to "image is removed"
        self.assertContains(response, "image is removed")

        # Verify image is removed
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile.profile_image)

    def test_image_not_removed_without_flag(self):
        """Test that image is not removed if remove_image flag is not set"""
        self.client.login(username="testuser", password="password123")

        # Submit form without remove_image flag
        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Updated Name",
                "about": "Test",
                "privacy": "PUBLIC",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        # Verify image still exists
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile.profile_image)

    def test_image_removal_with_other_changes(self):
        """Test that image removal works alongside other profile changes"""
        self.client.login(username="testuser", password="password123")

        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Updated Full Name",
                "about": "Updated about text",
                "privacy": "PRIVATE",
                "remove_image": "true",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        # Verify all changes were saved
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()

        self.assertFalse(self.user.profile.profile_image)
        self.assertEqual(self.user.profile.full_name, "Updated Full Name")
        self.assertEqual(self.user.profile.about, "Updated about text")
        self.assertEqual(self.user.profile.privacy, "PRIVATE")

    def test_edit_profile_page_has_removal_elements(self):
        """Test that edit profile page has removal UI elements"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="mark-for-removal-btn"')
        self.assertContains(response, 'id="undo-removal-btn"')
        self.assertContains(response, 'id="remove-image-input"')
        self.assertContains(response, 'id="removal-indicator"')

    def test_removal_indicator_text(self):
        """Test that removal indicator has correct text"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "This image will be removed when you save changes"
        )
        self.assertContains(response, "Undo")


class ImageRemovalUITests(TestCase):
    """Test UI elements for image removal"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

    def test_no_removal_ui_without_image(self):
        """Test that removal UI doesn't show when no image exists"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="mark-for-removal-btn"')

    def test_javascript_tracks_removal(self):
        """Test that JavaScript tracks image removal as form change"""
        # Create image first
        img = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)

        test_image = SimpleUploadedFile(
            name="test.png", content=img_io.read(), content_type="image/png"
        )

        self.user.profile.profile_image = test_image
        self.user.profile.save()

        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "imageMarkedForRemoval")
        self.assertContains(response, "formChanged = true")
