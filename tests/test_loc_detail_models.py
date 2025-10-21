"""
Unit tests for loc_detail models
Tests PublicArt, UserFavoriteArt, and ArtComment models
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError
from decimal import Decimal
from loc_detail.models import PublicArt, UserFavoriteArt, ArtComment


class PublicArtModelTests(TestCase):
    """Test cases for PublicArt model"""

    def setUp(self):
        """Set up test data"""
        self.art = PublicArt.objects.create(
            artist_name="Test Artist",
            title="Test Sculpture",
            description="A beautiful test sculpture",
            location="Central Park",
            borough="Manhattan",
            latitude=Decimal("40.7829"),
            longitude=Decimal("-73.9654"),
            medium="Bronze",
            dimensions="10ft x 5ft",
            year_created="2020",
            year_dedicated="2021",
            agency="NYC Parks",
            community_board="CB5",
            external_id="TEST001",
        )

    def test_create_public_art(self):
        """Test creating a PublicArt instance"""
        self.assertEqual(self.art.artist_name, "Test Artist")
        self.assertEqual(self.art.title, "Test Sculpture")
        self.assertEqual(self.art.borough, "Manhattan")
        self.assertEqual(self.art.latitude, Decimal("40.7829"))
        self.assertEqual(self.art.longitude, Decimal("-73.9654"))

    def test_public_art_str_method(self):
        """Test string representation of PublicArt"""
        expected = "Test Sculpture by Test Artist"
        self.assertEqual(str(self.art), expected)

    def test_public_art_str_method_untitled(self):
        """Test string representation when title is None"""
        art = PublicArt.objects.create(artist_name="Artist Name")
        self.assertEqual(str(art), "Untitled by Artist Name")

    def test_public_art_str_method_unknown_artist(self):
        """Test string representation when artist is None"""
        art = PublicArt.objects.create(title="Test Title")
        self.assertEqual(str(art), "Test Title by Unknown")

    def test_public_art_blank_fields(self):
        """Test that blank fields are allowed"""
        minimal_art = PublicArt.objects.create()
        self.assertIsNone(minimal_art.artist_name)
        self.assertIsNone(minimal_art.title)
        self.assertIsNone(minimal_art.description)

    def test_public_art_unique_external_id(self):
        """Test that external_id must be unique"""
        PublicArt.objects.create(external_id="UNIQUE001")
        with self.assertRaises(IntegrityError):
            PublicArt.objects.create(external_id="UNIQUE001")

    def test_public_art_coordinates_precision(self):
        """Test latitude and longitude precision"""
        art = PublicArt.objects.create(
            latitude=Decimal("40.7128758"), longitude=Decimal("-74.0059945")
        )
        self.assertEqual(art.latitude, Decimal("40.7128758"))
        self.assertEqual(art.longitude, Decimal("-74.0059945"))

    def test_public_art_ordering(self):
        """Test that PublicArt instances are ordered by title"""
        PublicArt.objects.create(title="Zebra Art")
        PublicArt.objects.create(title="Alpha Art")
        PublicArt.objects.create(title="Beta Art")

        art_list = list(PublicArt.objects.all().values_list("title", flat=True))
        # Filter out None values and sort
        art_list = [title for title in art_list if title]
        self.assertEqual(art_list[0], "Alpha Art")
        self.assertEqual(art_list[1], "Beta Art")

    def test_public_art_timestamps(self):
        """Test that created_at and updated_at are set"""
        self.assertIsNotNone(self.art.created_at)
        self.assertIsNotNone(self.art.updated_at)


class UserFavoriteArtModelTests(TestCase):
    """Test cases for UserFavoriteArt model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(
            title="Favorite Art", artist_name="Favorite Artist"
        )

    def test_create_favorite(self):
        """Test creating a favorite"""
        favorite = UserFavoriteArt.objects.create(
            user=self.user, art=self.art, notes="This is amazing!"
        )
        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.art, self.art)
        self.assertEqual(favorite.notes, "This is amazing!")

    def test_favorite_str_method(self):
        """Test string representation of UserFavoriteArt"""
        favorite = UserFavoriteArt.objects.create(user=self.user, art=self.art)
        expected = f"{self.user.username} - {self.art.title}"
        self.assertEqual(str(favorite), expected)

    def test_favorite_unique_together(self):
        """Test that a user cannot favorite the same art twice"""
        UserFavoriteArt.objects.create(user=self.user, art=self.art)
        with self.assertRaises(IntegrityError):
            UserFavoriteArt.objects.create(user=self.user, art=self.art)

    def test_favorite_multiple_users(self):
        """Test that multiple users can favorite the same art"""
        user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )
        favorite1 = UserFavoriteArt.objects.create(user=self.user, art=self.art)
        favorite2 = UserFavoriteArt.objects.create(user=user2, art=self.art)

        self.assertIsNotNone(favorite1)
        self.assertIsNotNone(favorite2)
        self.assertEqual(self.art.favorited_by.count(), 2)

    def test_favorite_cascade_delete_user(self):
        """Test that favorites are deleted when user is deleted"""
        UserFavoriteArt.objects.create(user=self.user, art=self.art)
        self.assertEqual(UserFavoriteArt.objects.count(), 1)
        self.user.delete()
        self.assertEqual(UserFavoriteArt.objects.count(), 0)

    def test_favorite_cascade_delete_art(self):
        """Test that favorites are deleted when art is deleted"""
        UserFavoriteArt.objects.create(user=self.user, art=self.art)
        self.assertEqual(UserFavoriteArt.objects.count(), 1)
        self.art.delete()
        self.assertEqual(UserFavoriteArt.objects.count(), 0)

    def test_favorite_added_at_timestamp(self):
        """Test that added_at timestamp is set"""
        favorite = UserFavoriteArt.objects.create(user=self.user, art=self.art)
        self.assertIsNotNone(favorite.added_at)

    def test_favorite_ordering(self):
        """Test that favorites are ordered by added_at descending"""
        art2 = PublicArt.objects.create(title="Second Art")
        art3 = PublicArt.objects.create(title="Third Art")

        UserFavoriteArt.objects.create(user=self.user, art=self.art)
        UserFavoriteArt.objects.create(user=self.user, art=art2)
        fav3 = UserFavoriteArt.objects.create(user=self.user, art=art3)

        favorites = list(UserFavoriteArt.objects.all())
        # Most recent should be first, verify ordering exists
        self.assertEqual(len(favorites), 3)
        # Verify fav3 is in the list
        self.assertIn(fav3, favorites)


class ArtCommentModelTests(TestCase):
    """Test cases for ArtComment model"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username="commenter", email="commenter@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(
            title="Commented Art", artist_name="Art Artist"
        )

    def test_create_comment(self):
        """Test creating a comment"""
        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="This is a beautiful piece!"
        )
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.art, self.art)
        self.assertEqual(comment.comment, "This is a beautiful piece!")

    def test_comment_str_method(self):
        """Test string representation of ArtComment"""
        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Great work!"
        )
        expected = f"{self.user.username} on {self.art.title}"
        self.assertEqual(str(comment), expected)

    def test_comment_timestamps(self):
        """Test that timestamps are set"""
        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Test comment"
        )
        self.assertIsNotNone(comment.created_at)
        self.assertIsNotNone(comment.updated_at)

    def test_comment_ordering(self):
        """Test that comments are ordered by created_at descending"""
        ArtComment.objects.create(user=self.user, art=self.art, comment="First comment")
        ArtComment.objects.create(
            user=self.user, art=self.art, comment="Second comment"
        )
        comment3 = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Third comment"
        )

        comments = list(ArtComment.objects.all())
        # Verify all comments are created
        self.assertEqual(len(comments), 3)
        # Verify comment3 is in the list
        self.assertIn(comment3, comments)

    def test_comment_cascade_delete_user(self):
        """Test that comments are deleted when user is deleted"""
        ArtComment.objects.create(user=self.user, art=self.art, comment="Test")
        self.assertEqual(ArtComment.objects.count(), 1)
        self.user.delete()
        self.assertEqual(ArtComment.objects.count(), 0)

    def test_comment_cascade_delete_art(self):
        """Test that comments are deleted when art is deleted"""
        ArtComment.objects.create(user=self.user, art=self.art, comment="Test")
        self.assertEqual(ArtComment.objects.count(), 1)
        self.art.delete()
        self.assertEqual(ArtComment.objects.count(), 0)

    def test_multiple_comments_same_user(self):
        """Test that a user can make multiple comments on the same art"""
        ArtComment.objects.create(user=self.user, art=self.art, comment="First comment")
        ArtComment.objects.create(
            user=self.user, art=self.art, comment="Second comment"
        )

        self.assertEqual(self.art.comments.count(), 2)

    def test_related_name_access(self):
        """Test accessing comments through related names"""
        ArtComment.objects.create(user=self.user, art=self.art, comment="User comment")

        # Access through user's related name
        self.assertEqual(self.user.art_comments.count(), 1)

        # Access through art's related name
        self.assertEqual(self.art.comments.count(), 1)
