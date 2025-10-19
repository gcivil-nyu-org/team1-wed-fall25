from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .forms import SignupForm


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
    def test_signup_creates_user(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "newpass123",
                "password2": "newpass123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "new@example.com")
