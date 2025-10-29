"""
Comprehensive unit tests for user_profile functionality
Improved coverage for views, models, and forms
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from datetime import timedelta

from user_profile.models import UserProfile
from user_profile.forms import UserProfileForm, UserBasicInfoForm
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

        Event.objects.create(
            title="Public Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=location,
        )

        Event.objects.create(
            title="Private Event",
            host=self.user,
            visibility=EventVisibility.PRIVATE,
            start_time=timezone.now() + timedelta(days=1),
            start_location=location,
        )

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

        self.assertEqual(self.user1.following.count(), 1)
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
        form = UserProfileForm(data={"about": "Test", "privacy": "PUBLIC"})
        self.assertIn("maxlength", str(form["about"]))

    def test_form_privacy_choices(self):
        """Test privacy field has correct choices"""
        form = UserProfileForm()
        choices = form.fields["privacy"].choices
        self.assertIn(("PUBLIC", "Public"), choices)
        self.assertIn(("PRIVATE", "Private"), choices)

    def test_form_clean_profile_image_too_large(self):
        """Test profile image size validation"""
        large_image = SimpleUploadedFile(
            name="large.jpg",
            content=b"x" * (6 * 1024 * 1024),  # 6MB
            content_type="image/jpeg",
        )

        # Create instance for form
        profile = UserProfile.objects.get(user=self.user)

        form = UserProfileForm(
            data={"privacy": "PUBLIC"},
            files={"profile_image": large_image},
            instance=profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("profile_image", form.errors)

    def test_form_clean_profile_image_valid(self):
        valid_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06"
            b"\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDAT"
            b"x\x9cc\x00\x01\x00\x00\x05\x00\x01"
            b"\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        small_image = SimpleUploadedFile(
            name="tiny.png",
            content=valid_png,
            content_type="image/png",
        )

        profile = UserProfile.objects.get(user=self.user)

        form = UserProfileForm(
            data={"privacy": "PUBLIC"},
            files={"profile_image": small_image},
            instance=profile,
        )

        # Should now validate correctly
        self.assertTrue(form.is_valid(), msg=form.errors)


class UserBasicInfoFormTests(TestCase):
    """Test cases for UserBasicInfoForm"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_form_valid_data(self):
        """Test form with valid data"""
        form = UserBasicInfoForm(
            data={"username": "testuser", "email": "newemail@example.com"},
            instance=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_form_duplicate_email(self):
        """Test email uniqueness validation"""
        User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )

        form = UserBasicInfoForm(
            data={"username": "testuser", "email": "other@example.com"},
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_form_email_case_insensitive(self):
        """Test email is converted to lowercase"""
        form = UserBasicInfoForm(
            data={"username": "testuser", "email": "TEST@EXAMPLE.COM"},
            instance=self.user,
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["email"], "test@example.com")


class ProfileViewTests(TestCase):
    """Test cases for profile_view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )
        self.location = PublicArt.objects.create(
            title="Art", latitude=40.7128, longitude=-74.0060
        )

    def test_profile_view_requires_login(self):
        """Test that profile view requires authentication"""
        response = self.client.get(
            reverse("user_profile:profile_view", kwargs={"username": "testuser"})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_view_own_profile(self):
        """Test viewing own profile"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("user_profile:profile_view", kwargs={"username": "testuser"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_own_profile"])
        self.assertIn("profile", response.context)

    def test_view_own_profile_without_username(self):
        """Test viewing own profile via /profile/ URL"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("user_profile:my_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_own_profile"])

    def test_view_other_public_profile(self):
        """Test viewing another user's public profile"""
        self.other_user.profile.privacy = "PUBLIC"
        self.other_user.profile.save()

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("user_profile:profile_view", kwargs={"username": "otheruser"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_own_profile"])

    def test_view_private_profile_denied(self):
        """Test that private profiles redirect"""
        self.other_user.profile.privacy = "PRIVATE"
        self.other_user.profile.save()

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("user_profile:profile_view", kwargs={"username": "otheruser"})
        )

        self.assertEqual(response.status_code, 302)

    def test_profile_shows_statistics(self):
        """Test that profile shows all statistics"""
        # Create favorite art
        art = PublicArt.objects.create(title="Test Art")
        UserFavoriteArt.objects.create(user=self.user, art=art)

        # Create hosted event
        Event.objects.create(
            title="Test Event",
            host=self.user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )

        # Create attended event
        other_event = Event.objects.create(
            title="Other Event",
            host=self.other_user,
            visibility=EventVisibility.PUBLIC_OPEN,
            start_time=timezone.now() + timedelta(days=1),
            start_location=self.location,
        )
        EventMembership.objects.create(
            event=other_event, user=self.user, role=MembershipRole.ATTENDEE
        )

        # Create follow relationships
        self.other_user.following.create(following=self.user)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("user_profile:profile_view", kwargs={"username": "testuser"})
        )

        self.assertEqual(response.context["favorite_art_count"], 1)
        self.assertEqual(response.context["followers_count"], 1)
        self.assertEqual(response.context["attended_events_count"], 1)
        self.assertEqual(len(response.context["hosted_events"]), 1)

    def test_profile_follow_status(self):
        """Test is_following status in context"""
        self.client.login(username="testuser", password="testpass123")

        # Not following initially
        response = self.client.get(
            reverse("user_profile:profile_view", kwargs={"username": "otheruser"})
        )
        self.assertFalse(response.context["is_following"])

        # Follow the user
        self.user.following.create(following=self.other_user)

        # Should show as following
        response = self.client.get(
            reverse("user_profile:profile_view", kwargs={"username": "otheruser"})
        )
        self.assertTrue(response.context["is_following"])

    def test_profile_404_for_nonexistent_user(self):
        """Test 404 for non-existent username"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("user_profile:profile_view", kwargs={"username": "nonexistent"})
        )
        self.assertEqual(response.status_code, 404)


class EditProfileViewTests(TestCase):
    """Test cases for edit_profile view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_edit_profile_requires_login(self):
        """Test that edit profile requires authentication"""
        response = self.client.get(reverse("user_profile:edit_profile"))
        self.assertEqual(response.status_code, 302)

    def test_edit_profile_get(self):
        """Test GET request to edit profile"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("user_profile:edit_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("profile_form", response.context)
        self.assertIn("user_form", response.context)

    def test_edit_profile_post_success(self):
        """Test successful profile update"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "newemail@example.com",
                "full_name": "Test User Full",
                "about": "Updated about",
                "contact_info": "contact@example.com",
                "privacy": "PRIVATE",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()

        self.assertEqual(self.user.email, "newemail@example.com")
        self.assertEqual(self.user.profile.full_name, "Test User Full")
        self.assertEqual(self.user.profile.privacy, "PRIVATE")

    def test_edit_profile_post_invalid(self):
        """Test profile update with invalid data"""
        User.objects.create_user(
            username="otheruser", email="other@example.com", password="testpass123"
        )

        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("user_profile:edit_profile"),
            {
                "username": "testuser",
                "email": "other@example.com",  # Duplicate email
                "full_name": "Test",
                "privacy": "PUBLIC",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("user_form", response.context)


class RemoveProfileImageViewTests(TestCase):
    """Test cases for remove_profile_image view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_remove_image_requires_login(self):
        """Test that remove image requires authentication"""
        response = self.client.post(reverse("user_profile:remove_profile_image"))
        self.assertEqual(response.status_code, 302)

    def test_remove_image_requires_post(self):
        """Test that remove image requires POST"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("user_profile:remove_profile_image"))
        self.assertEqual(response.status_code, 405)

    def test_remove_image_success(self):
        """Test successfully removing profile image"""
        image = SimpleUploadedFile(
            name="test.jpg", content=b"file_content", content_type="image/jpeg"
        )

        self.user.profile.profile_image = image
        self.user.profile.save()

        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("user_profile:remove_profile_image"))

        self.assertEqual(response.status_code, 302)

        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.profile_image)

    def test_remove_image_when_none(self):
        """Test removing image when no image exists"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("user_profile:remove_profile_image"))

        self.assertEqual(response.status_code, 302)


class FollowUserViewTests(TestCase):
    """Test cases for follow_user view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

    def test_follow_requires_login(self):
        """Test that follow requires authentication"""
        response = self.client.post(
            reverse("user_profile:follow_user", kwargs={"username": "user2"})
        )
        self.assertEqual(response.status_code, 302)

    def test_follow_requires_post(self):
        """Test that follow requires POST"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("user_profile:follow_user", kwargs={"username": "user2"})
        )
        self.assertEqual(response.status_code, 302)

    def test_follow_success(self):
        """Test successfully following a user"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_profile:follow_user", kwargs={"username": "user2"})
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.user1.following.filter(following=self.user2).exists())

    def test_cannot_follow_self(self):
        """Test that user cannot follow themselves"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_profile:follow_user", kwargs={"username": "user1"})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.user1.following.filter(following=self.user1).exists())

    def test_follow_already_following(self):
        """Test following when already following"""
        self.user1.following.create(following=self.user2)

        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_profile:follow_user", kwargs={"username": "user2"})
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user1.following.count(), 1)

    def test_follow_404_for_nonexistent_user(self):
        """Test 404 for non-existent user"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_profile:follow_user", kwargs={"username": "nonexistent"})
        )
        self.assertEqual(response.status_code, 404)


class UnfollowUserViewTests(TestCase):
    """Test cases for unfollow_user view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

    def test_unfollow_requires_login(self):
        """Test that unfollow requires authentication"""
        response = self.client.post(
            reverse("user_profile:unfollow_user", kwargs={"username": "user2"})
        )
        self.assertEqual(response.status_code, 302)

    def test_unfollow_requires_post(self):
        """Test that unfollow requires POST"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("user_profile:unfollow_user", kwargs={"username": "user2"})
        )
        self.assertEqual(response.status_code, 302)

    def test_unfollow_success(self):
        """Test successfully unfollowing"""
        self.user1.following.create(following=self.user2)

        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_profile:unfollow_user", kwargs={"username": "user2"})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.user1.following.filter(following=self.user2).exists())

    def test_unfollow_when_not_following(self):
        """Test unfollowing when not following"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("user_profile:unfollow_user", kwargs={"username": "user2"})
        )

        self.assertEqual(response.status_code, 302)


class FollowersListViewTests(TestCase):
    """Test cases for followers_list view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.follower = User.objects.create_user(
            username="follower", email="follower@example.com", password="testpass123"
        )

    def test_followers_list_requires_login(self):
        """Test that followers list requires authentication"""
        response = self.client.get(
            reverse("user_profile:followers_list", kwargs={"username": "testuser"})
        )
        self.assertEqual(response.status_code, 302)

    def test_followers_list_success(self):
        """Test viewing followers list"""
        self.follower.following.create(following=self.user)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("user_profile:followers_list", kwargs={"username": "testuser"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["list_type"], "followers")

    def test_followers_list_private_profile(self):
        """Test that private profile followers list is protected"""
        other_user = User.objects.create_user(
            username="other", email="other@example.com", password="testpass123"
        )
        other_user.profile.privacy = "PRIVATE"
        other_user.profile.save()

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("user_profile:followers_list", kwargs={"username": "other"})
        )

        self.assertEqual(response.status_code, 302)


class FollowingListViewTests(TestCase):
    """Test cases for following_list view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.following = User.objects.create_user(
            username="following", email="following@example.com", password="testpass123"
        )

    def test_following_list_requires_login(self):
        """Test that following list requires authentication"""
        response = self.client.get(
            reverse("user_profile:following_list", kwargs={"username": "testuser"})
        )
        self.assertEqual(response.status_code, 302)

    def test_following_list_success(self):
        """Test viewing following list"""
        self.user.following.create(following=self.following)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("user_profile:following_list", kwargs={"username": "testuser"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["list_type"], "following")


class UserSearchViewTests(TestCase):
    """Test cases for user_search view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="searcher", email="searcher@example.com", password="testpass123"
        )
        self.public_user = User.objects.create_user(
            username="publicuser", email="public@example.com", password="testpass123"
        )
        self.public_user.profile.full_name = "Public Test User"
        self.public_user.profile.privacy = "PUBLIC"
        self.public_user.profile.save()

        self.private_user = User.objects.create_user(
            username="privateuser",
            email="private@example.com",
            password="testpass123",
        )
        self.private_user.profile.privacy = "PRIVATE"
        self.private_user.profile.save()

    def test_user_search_requires_login(self):
        """Test that user search requires authentication"""
        response = self.client.get(reverse("user_profile:user_search"))
        self.assertEqual(response.status_code, 302)

    def test_user_search_by_username(self):
        """Test searching by username"""
        self.client.login(username="searcher", password="testpass123")
        response = self.client.get(reverse("user_profile:user_search"), {"q": "public"})

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.public_user, response.context["users"])

    def test_user_search_by_full_name(self):
        """Test searching by full name"""
        self.client.login(username="searcher", password="testpass123")
        response = self.client.get(
            reverse("user_profile:user_search"), {"q": "Test User"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.public_user, response.context["users"])

    def test_user_search_excludes_private(self):
        """Test that search excludes private profiles"""
        self.client.login(username="searcher", password="testpass123")
        response = self.client.get(reverse("user_profile:user_search"), {"q": "user"})

        self.assertIn(self.public_user, response.context["users"])
        self.assertNotIn(self.private_user, response.context["users"])

    def test_user_search_empty_query(self):
        """Test search with empty query"""
        self.client.login(username="searcher", password="testpass123")
        response = self.client.get(reverse("user_profile:user_search"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["users"]), 0)
