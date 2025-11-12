from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .forms import SignupForm, OTPVerificationForm
from .models import EmailVerificationOTP


class SignupFormTests(TestCase):
    def test_email_uniqueness_case_insensitive(self):
        User.objects.create_user(
            username="test1", email="test@example.com", password="pass123"
        )
        form = SignupForm(
            data={
                "username": "test2",
                "email": "TEST@example.com",
                "password1": "testpass123",
                "password2": "testpass123",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_email_lowercased_on_save(self):
        form = SignupForm(
            data={
                "username": "testuser",
                "email": "TEST@EXAMPLE.COM",
                "password1": "testpass123",
                "password2": "testpass123",
            }
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.email, "test@example.com")


class AuthBackendTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = Client()

    def test_login_with_username(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "testuser", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/artinerary/")

    def test_login_with_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "test@example.com", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/artinerary/")

    def test_login_with_wrong_password(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "testuser", "password": "wrongpass"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct")


class SignupViewTests(TestCase):
    def test_signup_redirects_to_otp_verification(self):
        """Test that signup redirects to OTP verification instead of
        creating user immediately"""
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "newpass123",
                "password2": "newpass123",
            },
        )
        # Should redirect to OTP verification page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:verify_otp"))

        # User should NOT be created yet (pending OTP verification)
        self.assertFalse(User.objects.filter(username="newuser").exists())

        # Session should contain pending verification email
        session = self.client.session
        self.assertEqual(session.get("pending_verification_email"), "new@example.com")


class EmailVerificationOTPModelTests(TestCase):
    def test_otp_generation(self):
        """Test OTP is automatically generated"""
        otp_record = EmailVerificationOTP.objects.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashedpassword",
        )
        self.assertIsNotNone(otp_record.otp)
        self.assertEqual(len(otp_record.otp), 6)
        self.assertTrue(otp_record.otp.isdigit())

    def test_otp_not_expired_immediately(self):
        """Test OTP is not expired immediately after creation"""
        otp_record = EmailVerificationOTP.objects.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashedpassword",
        )
        self.assertFalse(otp_record.is_expired())

    def test_otp_expired_after_3_minutes(self):
        """Test OTP is expired after 3 minutes"""
        otp_record = EmailVerificationOTP.objects.create(
            email="test@example.com",
            username="testuser",
            password_hash="hashedpassword",
        )
        # Simulate 3+ minutes passing
        otp_record.created_at = timezone.now() - timedelta(minutes=4)
        otp_record.save()
        self.assertTrue(otp_record.is_expired())


class OTPVerificationFormTests(TestCase):
    def test_valid_otp_form(self):
        """Test form accepts valid 6-digit OTP"""
        form = OTPVerificationForm(data={"otp": "123456"})
        self.assertTrue(form.is_valid())

    def test_invalid_otp_too_short(self):
        """Test form rejects OTP less than 6 digits"""
        form = OTPVerificationForm(data={"otp": "12345"})
        self.assertFalse(form.is_valid())

    def test_invalid_otp_too_long(self):
        """Test form rejects OTP more than 6 digits"""
        form = OTPVerificationForm(data={"otp": "1234567"})
        self.assertFalse(form.is_valid())

    def test_invalid_otp_non_numeric(self):
        """Test form rejects non-numeric OTP"""
        form = OTPVerificationForm(data={"otp": "12ab56"})
        self.assertFalse(form.is_valid())


class OTPVerificationViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_verify_otp_success(self):
        """Test successful OTP verification creates user and logs them in"""
        # Create OTP record
        otp_record = EmailVerificationOTP.objects.create(
            email="test@example.com",
            username="testuser",
            password_hash="pbkdf2_sha256$600000$test$hash",
            otp="123456",
        )

        # Set session
        session = self.client.session
        session["pending_verification_email"] = "test@example.com"
        session.save()

        # Verify OTP
        response = self.client.post(reverse("accounts:verify_otp"), {"otp": "123456"})

        # Should redirect to home
        self.assertEqual(response.status_code, 302)

        # User should be created
        self.assertTrue(User.objects.filter(username="testuser").exists())

        # OTP should be marked as verified
        otp_record.refresh_from_db()
        self.assertTrue(otp_record.is_verified)

    def test_verify_otp_invalid_code(self):
        """Test invalid OTP code shows error"""
        # Create OTP record
        EmailVerificationOTP.objects.create(
            email="test@example.com",
            username="testuser",
            password_hash="pbkdf2_sha256$600000$test$hash",
            otp="123456",
        )

        # Set session
        session = self.client.session
        session["pending_verification_email"] = "test@example.com"
        session.save()

        # Try wrong OTP
        response = self.client.post(reverse("accounts:verify_otp"), {"otp": "999999"})

        # Should stay on verification page
        self.assertEqual(response.status_code, 200)

        # User should NOT be created
        self.assertFalse(User.objects.filter(username="testuser").exists())

    def test_verify_otp_without_session(self):
        """Test OTP verification without session redirects to signup"""
        response = self.client.get(reverse("accounts:verify_otp"))

        # Should redirect to signup
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:signup"))

    def test_verify_expired_otp(self):
        """Test expired OTP is rejected"""
        # Create expired OTP record
        otp_record = EmailVerificationOTP.objects.create(
            email="test@example.com",
            username="testuser",
            password_hash="pbkdf2_sha256$600000$test$hash",
            otp="123456",
        )
        # Make it expired
        otp_record.created_at = timezone.now() - timedelta(minutes=4)
        otp_record.save()

        # Set session
        session = self.client.session
        session["pending_verification_email"] = "test@example.com"
        session.save()

        # Try to verify
        response = self.client.post(reverse("accounts:verify_otp"), {"otp": "123456"})

        # Should redirect to signup
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:signup"))

        # User should NOT be created
        self.assertFalse(User.objects.filter(username="testuser").exists())


class ResendOTPViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_resend_otp_generates_new_code(self):
        """Test resending OTP generates a new code"""
        # Create OTP record
        otp_record = EmailVerificationOTP.objects.create(
            email="test@example.com",
            username="testuser",
            password_hash="pbkdf2_sha256$600000$test$hash",
            otp="123456",
        )
        old_otp = otp_record.otp

        # Set session
        session = self.client.session
        session["pending_verification_email"] = "test@example.com"
        session.save()

        # Resend OTP
        response = self.client.get(reverse("accounts:resend_otp"))

        # Should redirect back to verify page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:verify_otp"))

        # OTP should be different
        otp_record.refresh_from_db()
        self.assertNotEqual(otp_record.otp, old_otp)

    def test_resend_otp_without_session(self):
        """Test resending OTP without session redirects to signup"""
        response = self.client.get(reverse("accounts:resend_otp"))

        # Should redirect to signup
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:signup"))
