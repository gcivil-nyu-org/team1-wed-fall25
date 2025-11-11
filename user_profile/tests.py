from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from accounts.models import EmailVerificationOTP
from allauth.socialaccount.models import SocialAccount


class EmailChangeOTPTests(TestCase):
    def setUp(self):
        self.client = Client()

    def login(self, username, password):
        return self.client.login(username=username, password=password)

    def test_email_change_requires_otp_for_non_oauth_user(self):
        user = User.objects.create_user(
            username="alice1", email="alice@old.com", password="password123"
        )
        self.login("alice1", "password123")
        new_email = "alice.new@example.com"
        url = reverse("user_profile:edit_profile")

        # Submit edit profile with new email
        # include profile fields so profile_form is valid
        resp = self.client.post(
            url,
            {
                "username": "alice1",
                "email": new_email,
                "full_name": "",
                "about": "",
                "contact_info": "",
                "privacy": "PUBLIC",
            },
        )
        # Redirects to verify page
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("user_profile:verify_email_change"), resp.url)

        # OTP record created
        otp_record = EmailVerificationOTP.objects.filter(
            email=new_email, is_verified=False
        ).first()
        self.assertIsNotNone(otp_record)

        # Verify using OTP
        verify_url = reverse("user_profile:verify_email_change")
        resp = self.client.post(verify_url, {"otp": otp_record.otp}, follow=True)
        self.assertContains(
            resp, "Your email has been updated and verified successfully."
        )

        # Refresh user from DB
        user.refresh_from_db()
        self.assertEqual(user.email, new_email)

        # OTP marked verified
        otp_record.refresh_from_db()
        self.assertTrue(otp_record.is_verified)

    def test_email_change_skips_for_oauth_user(self):
        user = User.objects.create_user(
            username="alice2", email="oauth.old@example.com", password="password123"
        )
        SocialAccount.objects.create(user=user, provider="google", uid="123")
        self.login("alice2", "password123")
        new_email = "oauth.new@example.com"
        url = reverse("user_profile:edit_profile")

        resp = self.client.post(
            url,
            {
                "username": "alice2",
                "email": new_email,
                "full_name": "",
                "about": "",
                "contact_info": "",
                "privacy": "PUBLIC",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        user.refresh_from_db()
        # Email should be updated immediately
        self.assertEqual(user.email, new_email)

        # No OTP record should be created
        self.assertFalse(
            EmailVerificationOTP.objects.filter(
                email=new_email, is_verified=False
            ).exists()
        )

    def test_resend_generates_new_code(self):
        User.objects.create_user(
            username="alice3", email="alice@old.com", password="password123"
        )
        self.login("alice3", "password123")
        new_email = "resend@example.com"
        url = reverse("user_profile:edit_profile")
        resp = self.client.post(
            url,
            {
                "username": "alice3",
                "email": new_email,
                "full_name": "",
                "about": "",
                "contact_info": "",
                "privacy": "PUBLIC",
            },
        )
        self.assertEqual(resp.status_code, 302)

        otp1 = EmailVerificationOTP.objects.filter(
            email=new_email, is_verified=False
        ).latest("created_at")
        resend_url = reverse("user_profile:resend_email_change_otp")
        resp = self.client.get(resend_url, follow=True)
        self.assertEqual(resp.status_code, 200)

        otp2 = EmailVerificationOTP.objects.filter(
            email=new_email, is_verified=False
        ).latest("created_at")
        self.assertNotEqual(otp1.otp, otp2.otp)

    def test_expired_otp_rejected(self):
        user = User.objects.create_user(
            username="alice4", email="alice@old.com", password="password123"
        )
        self.login("alice4", "password123")
        new_email = "expired@example.com"
        url = reverse("user_profile:edit_profile")
        resp = self.client.post(
            url,
            {
                "username": "alice4",
                "email": new_email,
                "full_name": "",
                "about": "",
                "contact_info": "",
                "privacy": "PUBLIC",
            },
        )
        self.assertEqual(resp.status_code, 302)

        otp = EmailVerificationOTP.objects.filter(
            email=new_email, is_verified=False
        ).latest("created_at")
        # expire it
        otp.created_at = timezone.now() - timedelta(minutes=4)
        otp.save()

        verify_url = reverse("user_profile:verify_email_change")
        resp = self.client.post(verify_url, {"otp": otp.otp}, follow=True)
        self.assertContains(resp, "OTP has expired")

        # Email should not have changed
        user.refresh_from_db()
        self.assertEqual(user.email, "alice@old.com")
