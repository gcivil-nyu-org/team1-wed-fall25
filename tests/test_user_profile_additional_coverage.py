"""
Additional comprehensive tests for user_profile/views.py
These tests target the uncovered lines to increase coverage from 76.67% to 90%+

Coverage targets based on the image:
- Lines 109-110: Exception handling in image deletion
- Lines 156-157: Exception handling in email sending
- Lines 168: Image removal with email change
- Lines 184: Image removal without email change
- Lines 222-223: Exception handling in remove_profile_image
- Lines 370-373: No pending email change in verify_email_change
- Lines 378-410: OTP verification paths (expired, invalid, success)
- Lines 424-466: Resend OTP functionality
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
import io
from PIL import Image

from user_profile.models import UserProfile
from accounts.models import EmailVerificationOTP
from allauth.socialaccount.models import SocialAccount


class EditProfileEmailChangeTests(TestCase):
    """Test email change functionality in edit_profile view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="old@example.com", password="testpass123"
        )
        # Use get_or_create since profile may be auto-created by signal
        self.profile, created = UserProfile.objects.get_or_create(user=self.user)

    def test_email_change_sends_otp(self):
        """Test that changing email sends OTP verification"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "newemail@example.com",
                "full_name": "Test User",
                "about": "About me",
                "privacy": "PUBLIC",
            },
            follow=True,
        )

        # Should redirect to OTP verification
        self.assertRedirects(response, reverse("user_profile:verify_email_change"))

        # OTP should be created
        self.assertTrue(
            EmailVerificationOTP.objects.filter(
                email="newemail@example.com", is_verified=False
            ).exists()
        )

        # Email should be sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verify", mail.outbox[0].subject.lower())

    def test_email_change_with_oauth_user_no_otp(self):
        """Test that OAuth users can change email without OTP"""
        # Create a social account for this user
        SocialAccount.objects.create(user=self.user, provider="google", uid="123456")

        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "newemail@example.com",
                "full_name": "Test User",
                "about": "About me",
                "privacy": "PUBLIC",
            },
            follow=True,
        )

        # Should redirect to profile, not OTP page
        self.assertRedirects(
            response,
            reverse("user_profile:profile_view", kwargs={"username": "testuser"}),
        )

        # Email should be changed immediately
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "newemail@example.com")

    def test_email_change_with_image_removal(self):
        """Test line 168: Image removal during email change"""
        # Create image
        img = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)
        test_image = SimpleUploadedFile(
            name="test.png", content=img_io.read(), content_type="image/png"
        )

        self.user.profile.profile_image = test_image
        self.user.profile.save()

        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "newemail@example.com",
                "full_name": "Test User",
                "about": "About me",
                "privacy": "PUBLIC",
                "remove_image": "true",
            },
            follow=True,
        )

        # Should redirect to OTP verification
        self.assertRedirects(response, reverse("user_profile:verify_email_change"))

        # Image should be removed even before email is verified
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.profile_image)

    def test_email_send_exception_handling(self):
        """Test line 156-157: Email sending exception handling"""
        self.client.login(username="testuser", password="testpass123")

        with patch("user_profile.views.send_mail") as mock_send_mail:
            mock_send_mail.side_effect = Exception("Email server error")

            response = self.client.post(
                reverse("user_profile:edit_profile"),
                {
                    "username": "testuser",
                    "email": "newemail@example.com",
                    "full_name": "Test User",
                    "about": "About me",
                    "privacy": "PUBLIC",
                },
                follow=True,
            )

            # Should still redirect to verification even if email fails
            self.assertRedirects(response, reverse("user_profile:verify_email_change"))


class RemoveProfileImageExceptionTests(TestCase):
    """Test exception handling in remove_profile_image view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.profile, created = UserProfile.objects.get_or_create(user=self.user)

    def test_image_deletion_exception_handling(self):
        """Test lines 222-223: Exception during image file deletion"""
        # Create a mock image
        img = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)
        test_image = SimpleUploadedFile(
            name="test.png", content=img_io.read(), content_type="image/png"
        )

        self.user.profile.profile_image = test_image
        self.user.profile.save()

        self.client.login(username="testuser", password="testpass123")

        # Mock the delete method to raise an exception
        with patch.object(self.user.profile.profile_image, "delete") as mock_delete:
            mock_delete.side_effect = Exception("Storage error")

            response = self.client.post(
                reverse("user_profile:remove_profile_image"), follow=True
            )

            # Should still succeed and set image to None
            self.assertEqual(response.status_code, 200)
            self.user.profile.refresh_from_db()
            self.assertFalse(self.user.profile.profile_image)


class VerifyEmailChangeTests(TestCase):
    """Test email verification functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="old@example.com", password="testpass123"
        )

    def test_no_pending_email_change(self):
        """Test lines 370-373: Accessing verify page without pending change"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse("user_profile:verify_email_change"), follow=True
        )

        # Should redirect to edit_profile
        self.assertRedirects(response, reverse("user_profile:edit_profile"))
        self.assertContains(response, "No pending email change found")

    def test_otp_verification_success(self):
        """Test lines 394-407: Successful OTP verification"""
        self.client.login(username="testuser", password="testpass123")

        # Create OTP record
        otp_record = EmailVerificationOTP.objects.create(
            email="newemail@example.com", username="testuser", password_hash=""
        )

        # Set session
        session = self.client.session
        session["pending_email_change"] = "newemail@example.com"
        session.save()

        # Submit OTP
        response = self.client.post(
            reverse("user_profile:verify_email_change"),
            {"otp": otp_record.otp},
            follow=True,
        )

        # Should redirect to profile
        self.assertRedirects(
            response,
            reverse("user_profile:profile_view", kwargs={"username": "testuser"}),
        )

        # Email should be updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "newemail@example.com")

        # OTP should be marked verified
        otp_record.refresh_from_db()
        self.assertTrue(otp_record.is_verified)

        # Session should be cleared
        self.assertNotIn("pending_email_change", self.client.session)

    def test_expired_otp(self):
        """Test lines 384-392: Expired OTP handling"""
        self.client.login(username="testuser", password="testpass123")

        # Create expired OTP
        otp_record = EmailVerificationOTP.objects.create(
            email="newemail@example.com", username="testuser", password_hash=""
        )
        # Make it expired
        otp_record.created_at = timezone.now() - timedelta(minutes=10)
        otp_record.save()

        # Set session
        session = self.client.session
        session["pending_email_change"] = "newemail@example.com"
        session.save()

        response = self.client.post(
            reverse("user_profile:verify_email_change"),
            {"otp": otp_record.otp},
            follow=True,
        )

        # Should redirect to edit_profile
        self.assertRedirects(response, reverse("user_profile:edit_profile"))
        self.assertContains(response, "OTP has expired")

        # OTP should be deleted
        self.assertFalse(EmailVerificationOTP.objects.filter(id=otp_record.id).exists())

    def test_invalid_otp(self):
        """Test lines 409-410: Invalid OTP handling"""
        self.client.login(username="testuser", password="testpass123")

        # Create OTP record
        EmailVerificationOTP.objects.create(
            email="newemail@example.com", username="testuser", password_hash=""
        )

        # Set session
        session = self.client.session
        session["pending_email_change"] = "newemail@example.com"
        session.save()

        # Submit wrong OTP
        response = self.client.post(
            reverse("user_profile:verify_email_change"),
            {"otp": "999999"},  # Wrong OTP
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid verification code")


class ResendEmailChangeOTPTests(TestCase):
    """Test OTP resend functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="old@example.com", password="testpass123"
        )

    def test_resend_otp_no_pending_change(self):
        """Test lines 426-430: Resend without pending email change"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse("user_profile:resend_email_change_otp"), follow=True
        )

        self.assertRedirects(response, reverse("user_profile:edit_profile"))
        self.assertContains(response, "No pending email change found")

    def test_resend_otp_success(self):
        """Test lines 432-459: Successful OTP resend"""
        self.client.login(username="testuser", password="testpass123")

        # Create OTP record
        otp_record = EmailVerificationOTP.objects.create(
            email="newemail@example.com", username="testuser", password_hash=""
        )
        old_otp = otp_record.otp

        # Set session
        session = self.client.session
        session["pending_email_change"] = "newemail@example.com"
        session.save()

        # Clear mail outbox
        mail.outbox = []

        response = self.client.get(
            reverse("user_profile:resend_email_change_otp"), follow=True
        )

        # Should redirect back to verify page
        self.assertRedirects(response, reverse("user_profile:verify_email_change"))
        self.assertContains(response, "new verification code has been sent")

        # OTP should be regenerated
        otp_record.refresh_from_db()
        self.assertNotEqual(otp_record.otp, old_otp)

        # Email should be sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("new verification code", mail.outbox[0].subject.lower())

    def test_resend_otp_no_existing_record(self):
        """Test lines 460-464: Resend when OTP record doesn't exist"""
        self.client.login(username="testuser", password="testpass123")

        # Set session but don't create OTP record
        session = self.client.session
        session["pending_email_change"] = "newemail@example.com"
        session.save()

        response = self.client.get(
            reverse("user_profile:resend_email_change_otp"), follow=True
        )

        self.assertRedirects(response, reverse("user_profile:edit_profile"))
        self.assertContains(response, "Verification session expired")

    def test_resend_otp_email_exception(self):
        """Test lines 454-455: Email sending exception during resend"""
        self.client.login(username="testuser", password="testpass123")

        # Create OTP record
        EmailVerificationOTP.objects.create(
            email="newemail@example.com", username="testuser", password_hash=""
        )

        # Set session
        session = self.client.session
        session["pending_email_change"] = "newemail@example.com"
        session.save()

        with patch("user_profile.views.send_mail") as mock_send_mail:
            mock_send_mail.side_effect = Exception("Email server error")

            response = self.client.get(
                reverse("user_profile:resend_email_change_otp"), follow=True
            )

            # Should still show success message even if email fails
            self.assertEqual(response.status_code, 200)


class EditProfileImageDeletionExceptionTests(TestCase):
    """Test exception handling in edit_profile image deletion"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.profile, created = UserProfile.objects.get_or_create(user=self.user)

    def test_image_deletion_exception_in_edit_profile(self):
        """Test lines 109-110: Exception handling during image deletion in profile"""
        # Create image
        img = Image.new("RGB", (100, 100), color="red")
        img_io = io.BytesIO()
        img.save(img_io, format="PNG")
        img_io.seek(0)
        test_image = SimpleUploadedFile(
            name="test.png", content=img_io.read(), content_type="image/png"
        )

        self.user.profile.profile_image = test_image
        self.user.profile.save()

        self.client.login(username="testuser", password="testpass123")

        # Mock the delete method to raise an exception
        with patch.object(self.user.profile.profile_image, "delete") as mock_delete:
            mock_delete.side_effect = Exception("Storage error")

            response = self.client.post(
                reverse("user_profile:edit_profile"),
                {
                    "username": "testuser",
                    "email": "test@example.com",
                    "full_name": "Test User",
                    "about": "About me",
                    "privacy": "PUBLIC",
                    "remove_image": "true",
                },
                follow=True,
            )

            # Should still succeed
            self.assertEqual(response.status_code, 200)
            # Image should be set to None despite exception
            self.user.profile.refresh_from_db()
            self.assertFalse(self.user.profile.profile_image)
