"""
Unit tests for user_profile functionality
Tests models, views, and forms for user profiles and follow system
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from user_profile.forms import UserProfileForm  # Removed unused imports
from events.models import Event, EventMembership
from events.enums import EventVisibility, MembershipRole
from loc_detail.models import PublicArt, UserFavoriteArt


class UserProfileModelTests(TestCase):
    """Test cases for UserProfile model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_profile_auto_created(self):
        """Test that profile is automatically created when user is created"""
        self.assertTrue(hasattr(self.user, "profile"))
        self.assertIsNotNone(self.user.profile)

    def test_profile_str_method(self):
        """Test string representation of UserProfile"""
        expected = f"{self.user.username}'s Profile"
        self.assertEqual(str(self.user.profile), expected)

    def test_profile_default_privacy(self):
        """Test that default privacy is PUBLIC"""
        self.assertEqual(self.user.profile.privacy, "PUBLIC")
        self.assertTrue(self.user.profile.is_public())

    def test_profile_is_public_method(self):
        """Test is_public method"""
        self.user.profile.privacy = "PUBLIC"
        self.user.profile.save()
        self.assertTrue(self.user.profile.is_public())

        self.user.profile.privacy = "PRIVATE"
        self.user.profile.save()
        self.assertFalse(self.user.profile.is_public())

    def test_profile_full_name(self):
        """Test setting full name"""
        self.user.profile.full_name = "Test User Full"
        self.user.profile.save()
        self.assertEqual(self.user.profile.full_name, "Test User Full")

    def test_profile_about(self):
        """Test setting about section"""
        about_text = "I love art and exploring NYC!"
        self.user.profile.about = about_text
        self.user.profile.save()
        self.assertEqual(self.user.profile.about, about_text)

    def test_profile_contact_info(self):
        """Test setting contact info"""
        contact = "contact@example.com"
        self.user.profile.contact_info = contact
        self.user.profile.save()
        self.assertEqual(self.user.profile.contact_info, contact)

    def test_get_hosted_events_count(self):
        """Test counting hosted public events"""
        location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )

        # Create public event
        Event.objects.create(
            title="Public Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=location,
        )

        # Create private event (should not count)
        Event.objects.create(
            title="Private Event",
            host=self.user,
            visibility=EventVisibility.PRIVATE,
            start_time=timezone.now() + timedelta(days=1),
            start_location=location,
        )

        # Create deleted event (should not count)
        Event.objects.create(
            title="Deleted Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=location,
            is_deleted=True,
        )

        self.assertEqual(self.user.profile.get_hosted_events_count(), 1)


class UserFollowModelTests(TestCase):
    """Test cases for UserFollow model"""

    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

    def test_create_follow(self):
        """Test creating a follow relationship"""
        follow = self.user1.following.create(following=self.user2)
        self.assertEqual(follow.follower, self.user1)
        self.assertEqual(follow.following, self.user2)

    def test_follow_str_method(self):
        """Test string representation of UserFollow"""
        follow = self.user1.following.create(following=self.user2)
        expected = f"{self.user1.username} follows {self.user2.username}"
        self.assertEqual(str(follow), expected)

    def test_follow_unique_together(self):
        """Test that a user can't follow the same user twice"""
        self.user1.following.create(following=self.user2)

        with self.assertRaises(Exception):
            self.user1.following.create(following=self.user2)

    def test_follow_cascade_delete(self):
        """Test that follows are deleted when user is deleted"""
        self.user1.following.create(following=self.user2)
        self.assertEqual(self.user1.following.count(), 1)

        self.user1.delete()
        self.assertEqual(self.user2.followers.count(), 0)

    def test_related_names(self):
        """Test related name access"""
        self.user1.following.create(following=self.user2)

        # user1 is following user2
        self.assertEqual(self.user1.following.count(), 1)

        # user2 has user1 as a follower
        self.assertEqual(self.user2.followers.count(), 1)


class UserProfileFormTests(TestCase):
    """Test cases for UserProfileForm"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_form_valid_data(self):
        """Test form with valid data"""
        form = UserProfileForm(
            data={
                "full_name": "Test User",
                "about": "I love art!",
                "contact_info": "test@example.com",
                "privacy": "PUBLIC",
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_about_max_length(self):
        """Test about field max length validation"""
        long_text = "a" * 501
        form = UserProfileForm(data={"about": long_text, "privacy": "PUBLIC"})
        # Form should still validate (HTML maxlength handles this)
        # But the widget has maxlength attribute
        self.assertIn("maxlength", str(form["about"]))

    def test_form_privacy_choices(self):
        """Test privacy field has correct choices"""
        form = UserProfileForm()
        choices = form.fields["privacy"].choices
        self.assertIn(("PUBLIC", "Public"), choices)
        self.assertIn(("PRIVATE", "Private"), choices)


class UserProfileViewTests(TestCase):
    """Test cases for user profile views"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )

    def test_profile_view_requires_login(self):
        """Test that profile view requires authentication"""
        response = self.client.get(
            reverse(
                "user_profile:profile_view", kwargs={"username": self.user.username}
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_view_own_profile(self):
        """Test viewing own profile"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "user_profile:profile_view", kwargs={"username": self.user.username}
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user_profile/profile.html")
        self.assertTrue(response.context["is_own_profile"])

    def test_view_other_public_profile(self):
        """Test viewing another user's public profile"""
        self.other_user.profile.privacy = "PUBLIC"
        self.other_user.profile.save()

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "user_profile:profile_view",
                kwargs={"username": self.other_user.username},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_own_profile"])

    def test_view_private_profile_denied(self):
        """Test that private profiles can't be viewed by others"""
        self.other_user.profile.privacy = "PRIVATE"
        self.other_user.profile.save()

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "user_profile:profile_view",
                kwargs={"username": self.other_user.username},
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_profile_shows_hosted_events(self):
        """Test that profile shows hosted events"""
        location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )

        event = Event.objects.create(
            title="Test Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=location,
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "user_profile:profile_view", kwargs={"username": self.user.username}
            )
        )

        self.assertIn(event, response.context["hosted_events"])

    def test_edit_profile_requires_login(self):
        """Test that edit profile requires authentication"""
        response = self.client.get(reverse("user_profile:edit_profile"))
        self.assertEqual(response.status_code, 302)

    def test_edit_profile_view(self):
        """Test edit profile view"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user_profile/edit_profile.html")
        self.assertIn("profile_form", response.context)
        self.assertIn("user_form", response.context)

    def test_edit_profile_post(self):
        """Test updating profile via POST"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "newemail@example.com",
                "full_name": "Test User Full",
                "about": "Updated about section",
                "contact_info": "contact@example.com",
                "privacy": "PRIVATE",
            },
        )

        # Should redirect to profile
        self.assertEqual(response.status_code, 302)

        # Check that profile was updated
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()

        self.assertEqual(self.user.email, "newemail@example.com")
        self.assertEqual(self.user.profile.full_name, "Test User Full")
        self.assertEqual(self.user.profile.about, "Updated about section")
        self.assertEqual(self.user.profile.privacy, "PRIVATE")


class FollowFunctionalityTests(TestCase):
    """Test cases for follow/unfollow functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

    def test_follow_user_requires_login(self):
        """Test that following requires authentication"""
        response = self.client.post(
            reverse(
                "user_profile:follow_user", kwargs={"username": self.user2.username}
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_follow_user_requires_post(self):
        """Test that following requires POST method"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse(
                "user_profile:follow_user", kwargs={"username": self.user2.username}
            )
        )
        # Should redirect, not allow GET
        self.assertEqual(response.status_code, 302)

    def test_follow_user_success(self):
        """Test successfully following a user"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse(
                "user_profile:follow_user", kwargs={"username": self.user2.username}
            )
        )

        self.assertEqual(response.status_code, 302)

        # Check that follow was created
        self.assertTrue(self.user1.following.filter(following=self.user2).exists())

    def test_cannot_follow_self(self):
        """Test that user cannot follow themselves"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse(
                "user_profile:follow_user", kwargs={"username": self.user1.username}
            )
        )
        self.assertEqual(response.status_code, 302)

        # Should not create follow
        self.assertFalse(self.user1.following.filter(following=self.user1).exists())

    def test_unfollow_user(self):
        """Test unfollowing a user"""
        # Create follow
        self.user1.following.create(following=self.user2)

        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse(
                "user_profile:unfollow_user", kwargs={"username": self.user2.username}
            )
        )

        self.assertEqual(response.status_code, 302)

        # Check that follow was deleted
        self.assertFalse(self.user1.following.filter(following=self.user2).exists())

    def test_followers_list_view(self):
        """Test viewing followers list"""
        self.user1.following.create(following=self.user2)

        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse(
                "user_profile:followers_list", kwargs={"username": self.user2.username}
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user_profile/follow_list.html")

    def test_following_list_view(self):
        """Test viewing following list"""
        self.user1.following.create(following=self.user2)

        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse(
                "user_profile:following_list", kwargs={"username": self.user1.username}
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "user_profile/follow_list.html")

    def test_followers_list_private_profile(self):
        """Test that private profile followers list is protected"""
        self.user2.profile.privacy = "PRIVATE"
        self.user2.profile.save()

        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse(
                "user_profile:followers_list", kwargs={"username": self.user2.username}
            )
        )

        # Should redirect (privacy protection)
        self.assertEqual(response.status_code, 302)


class UserSearchTests(TestCase):
    """Test cases for user search functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create searchable users
        self.public_user = User.objects.create_user(
            username="publicuser", email="public@example.com", password="testpass123"
        )
        self.public_user.profile.full_name = "Public User Full"
        self.public_user.profile.privacy = "PUBLIC"
        self.public_user.profile.save()

        self.private_user = User.objects.create_user(
            username="privateuser", email="private@example.com", password="testpass123"
        )
        self.private_user.profile.privacy = "PRIVATE"
        self.private_user.profile.save()

    def test_user_search_requires_login(self):
        """Test that user search requires authentication"""
        response = self.client.get(reverse("user_profile:user_search"))
        self.assertEqual(response.status_code, 302)

    def test_user_search_by_username(self):
        """Test searching users by username"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("user_profile:user_search"), {"q": "public"})

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.public_user, response.context["users"])

    def test_user_search_by_full_name(self):
        """Test searching users by full name"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("user_profile:user_search"), {"q": "Public User"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.public_user, response.context["users"])

    def test_user_search_excludes_private(self):
        """Test that search only returns public profiles"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("user_profile:user_search"), {"q": "user"})

        # Should include public user but not private user
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.public_user, response.context["users"])
        self.assertNotIn(self.private_user, response.context["users"])

    def test_user_search_empty_query(self):
        """Test search with empty query"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("user_profile:user_search"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["users"]), 0)


class ProfileStatisticsTests(TestCase):
    """Test cases for profile statistics"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )

    def test_hosted_events_count(self):
        """Test counting hosted events"""
        # Create events
        Event.objects.create(
            title="Event 1",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        Event.objects.create(
            title="Event 2",
            host=self.user,
            visibility=EventVisibility.PUBLIC_INVITE,
            start_time=timezone.now() + timedelta(days=2),
            start_location=self.location,
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "user_profile:profile_view", kwargs={"username": self.user.username}
            )
        )

        self.assertEqual(len(response.context["hosted_events"]), 2)

    def test_favorite_art_count(self):
        """Test counting favorite artworks"""
        art1 = PublicArt.objects.create(title="Art 1")
        art2 = PublicArt.objects.create(title="Art 2")

        UserFavoriteArt.objects.create(user=self.user, art=art1)
        UserFavoriteArt.objects.create(user=self.user, art=art2)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "user_profile:profile_view", kwargs={"username": self.user.username}
            )
        )

        self.assertEqual(response.context["favorite_art_count"], 2)

    def test_attended_events_count(self):
        """Test counting attended events"""
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )

        event = Event.objects.create(
            title="Event",
            host=other_user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

        EventMembership.objects.create(
            event=event, user=self.user, role=MembershipRole.ATTENDEE
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "user_profile:profile_view", kwargs={"username": self.user.username}
            )
        )

        self.assertEqual(response.context["attended_events_count"], 1)

    def test_followers_following_count(self):
        """Test counting followers and following"""
        user2 = User.objects.create_user(username="user2", password="testpass123")
        user3 = User.objects.create_user(username="user3", password="testpass123")

        # user2 follows testuser
        user2.following.create(following=self.user)

        # testuser follows user3
        self.user.following.create(following=user3)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "user_profile:profile_view", kwargs={"username": self.user.username}
            )
        )

        self.assertEqual(response.context["followers_count"], 1)
        self.assertEqual(response.context["following_count"], 1)
