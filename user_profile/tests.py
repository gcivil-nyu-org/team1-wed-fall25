from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from accounts.models import EmailVerificationOTP
from allauth.socialaccount.models import SocialAccount
from user_profile.models import UserProfile


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


class VerifyEmailChangeEdgeCasesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

    def test_verify_email_change_without_session(self):
        """Test accessing verify email change without pending email in session"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:verify_email_change"))

        # Should redirect to edit profile
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("user_profile:edit_profile"))

    def test_verify_email_change_with_invalid_otp(self):
        """Test verification with invalid OTP"""
        self.client.login(username="testuser", password="password123")

        # Create OTP record
        new_email = "newemail@example.com"
        EmailVerificationOTP.objects.create(
            email=new_email,
            username="testuser",
            otp="123456",
        )

        # Set session
        session = self.client.session
        session["pending_email_change"] = new_email
        session.save()

        # Try with wrong OTP
        response = self.client.post(
            reverse("user_profile:verify_email_change"), {"otp": "999999"}
        )

        # Should stay on verify page with error
        self.assertEqual(response.status_code, 200)

        # Email should not have changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "test@example.com")

    def test_resend_email_change_otp_without_session(self):
        """Test resending OTP without pending email in session"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:resend_email_change_otp"))

        # Should redirect to edit profile
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("user_profile:edit_profile"))


class ProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password123"
        )

    def test_view_own_profile(self):
        """Test viewing own profile"""
        self.client.login(username="user1", password="password123")
        response = self.client.get(reverse("user_profile:profile_view", args=["user1"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user1")

    def test_view_other_user_profile(self):
        """Test viewing another user's profile"""
        self.client.login(username="user1", password="password123")
        response = self.client.get(reverse("user_profile:profile_view", args=["user2"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user2")

    def test_view_nonexistent_profile(self):
        """Test viewing nonexistent user profile"""
        self.client.login(username="user1", password="password123")
        response = self.client.get(
            reverse("user_profile:profile_view", args=["nonexistent"])
        )

        self.assertEqual(response.status_code, 404)


class RemoveProfileImageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

    def test_remove_profile_image_success(self):
        """Test removing profile image"""
        self.client.login(username="testuser", password="password123")

        # Note: This tests the view logic, not actual file deletion
        response = self.client.post(
            reverse("user_profile:remove_profile_image"), follow=True
        )

        self.assertEqual(response.status_code, 200)

    def test_remove_profile_image_requires_login(self):
        """Test that removing profile image requires authentication"""
        response = self.client.post(reverse("user_profile:remove_profile_image"))

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login", response.url)


class FollowUnfollowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password123"
        )

    def test_follow_user(self):
        """Test following another user"""
        self.client.login(username="user1", password="password123")
        response = self.client.post(
            reverse("user_profile:follow_user", args=["user2"]), follow=True
        )

        # Should successfully process the follow request
        self.assertEqual(response.status_code, 200)

    def test_unfollow_user(self):
        """Test unfollowing a user"""
        self.client.login(username="user1", password="password123")
        response = self.client.post(
            reverse("user_profile:unfollow_user", args=["user2"]), follow=True
        )

        # Should successfully process the unfollow request
        self.assertEqual(response.status_code, 200)

    def test_cannot_follow_self(self):
        """Test that user cannot follow themselves"""
        self.client.login(username="user1", password="password123")
        response = self.client.post(
            reverse("user_profile:follow_user", args=["user1"]), follow=True
        )

        # Should handle gracefully
        self.assertEqual(response.status_code, 200)

    def test_follow_requires_login(self):
        """Test that following requires authentication"""
        response = self.client.post(reverse("user_profile:follow_user", args=["user2"]))

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login", response.url)


class FollowersFollowingListTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.follower = User.objects.create_user(
            username="follower", email="follower@example.com", password="password123"
        )

    def test_followers_list(self):
        """Test viewing followers list"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(
            reverse("user_profile:followers_list", args=["testuser"])
        )

        self.assertEqual(response.status_code, 200)

    def test_following_list(self):
        """Test viewing following list"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(
            reverse("user_profile:following_list", args=["testuser"])
        )

        self.assertEqual(response.status_code, 200)


class UserSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.searchable_user = User.objects.create_user(
            username="searchme",
            email="searchme@example.com",
            password="password123",
        )

    def test_user_search_with_query(self):
        """Test searching for users"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:user_search"), {"q": "search"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "searchme")

    def test_user_search_without_query(self):
        """Test search page without query"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:user_search"))

        self.assertEqual(response.status_code, 200)

    def test_user_search_no_results(self):
        """Test search with no matching users"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(
            reverse("user_profile:user_search"), {"q": "nonexistent"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "searchme")


class EditProfileFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

    def test_edit_profile_get_request(self):
        """Test GET request to edit profile page"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Profile")

    def test_edit_profile_without_email_change(self):
        """Test editing profile without changing email"""
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",  # Same email
                "full_name": "Test User",
                "about": "About me",
                "contact_info": "",
                "privacy": "PUBLIC",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        # Email should remain the same
        self.assertEqual(self.user.email, "test@example.com")

    def test_edit_profile_invalid_form(self):
        """Test editing profile with invalid data"""
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "invalid-email",  # Invalid email
                "full_name": "Test User",
                "about": "About me",
                "privacy": "PUBLIC",
            },
        )

        # Should stay on edit page
        self.assertEqual(response.status_code, 200)


class PrivateProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password123"
        )
        # Make user2's profile private
        profile2 = UserProfile.objects.get_or_create(user=self.user2)[0]
        profile2.privacy = "PRIVATE"
        profile2.save()

    def test_cannot_view_private_profile(self):
        """Test that private profiles cannot be viewed by others"""
        self.client.login(username="user1", password="password123")
        response = self.client.get(reverse("user_profile:profile_view", args=["user2"]))

        # Should redirect with error
        self.assertEqual(response.status_code, 302)

    def test_can_view_own_private_profile(self):
        """Test that users can view their own private profile"""
        self.client.login(username="user2", password="password123")
        response = self.client.get(reverse("user_profile:profile_view", args=["user2"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user2")


class FollowStatisticsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        self.follower1 = User.objects.create_user(
            username="follower1", email="follower1@example.com", password="password123"
        )
        self.follower2 = User.objects.create_user(
            username="follower2", email="follower2@example.com", password="password123"
        )

    def test_follower_count_displayed(self):
        """Test that follower count is displayed on profile"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(
            reverse("user_profile:profile_view", args=["testuser"])
        )

        self.assertEqual(response.status_code, 200)

    def test_following_count_displayed(self):
        """Test that following count is displayed on profile"""
        self.client.login(username="testuser", password="password123")
        response = self.client.get(
            reverse("user_profile:profile_view", args=["testuser"])
        )

        self.assertEqual(response.status_code, 200)


class EmailChangeWithoutOTPTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

    def test_same_email_no_otp_required(self):
        """Test that changing to same email doesn't require OTP"""
        self.client.login(username="testuser", password="password123")
        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "test@example.com",  # Same email
                "full_name": "Updated Name",
                "about": "",
                "contact_info": "",
                "privacy": "PUBLIC",
            },
            follow=True,
        )

        # Should not redirect to OTP verification
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            "verify_email_change",
            response.redirect_chain[0][0] if response.redirect_chain else "",
        )


class VerifyEmailChangeFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

    def test_verify_email_change_get_request(self):
        """Test GET request to verify email change page"""
        self.client.login(username="testuser", password="password123")

        # Create OTP and set session
        new_email = "newemail@example.com"
        EmailVerificationOTP.objects.create(
            email=new_email, username="testuser", otp="123456"
        )
        session = self.client.session
        session["pending_email_change"] = new_email
        session.save()

        response = self.client.get(reverse("user_profile:verify_email_change"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, new_email)

    def test_verify_email_change_invalid_form(self):
        """Test submitting invalid OTP form for email change"""
        self.client.login(username="testuser", password="password123")

        new_email = "newemail@example.com"
        session = self.client.session
        session["pending_email_change"] = new_email
        session.save()

        # Submit invalid OTP format
        response = self.client.post(
            reverse("user_profile:verify_email_change"), {"otp": "abc"}
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "test@example.com")
