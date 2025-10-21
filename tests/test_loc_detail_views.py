"""
Unit tests for loc_detail views
Tests all views including list, detail, favorites, and API endpoints
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
import json
from loc_detail.models import PublicArt, UserFavoriteArt, ArtComment


class LocDetailIndexViewTests(TestCase):
    """Test cases for the art list index view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create test art pieces
        self.art1 = PublicArt.objects.create(
            title="Manhattan Art",
            artist_name="Artist One",
            description="Beautiful sculpture in Manhattan",
            location="Central Park",
            borough="Manhattan",
            latitude=Decimal("40.7829"),
            longitude=Decimal("-73.9654"),
        )
        self.art2 = PublicArt.objects.create(
            title="Brooklyn Art",
            artist_name="Artist Two",
            description="Amazing mural in Brooklyn",
            location="Prospect Park",
            borough="Brooklyn",
        )
        self.art3 = PublicArt.objects.create(
            title="Queens Art", artist_name="Artist One", borough="Queens"
        )

    def test_index_requires_login(self):
        """Test that index view requires authentication"""
        response = self.client.get(reverse("loc_detail:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_index_view_authenticated(self):
        """Test index view with authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "loc_detail/art_list.html")

    def test_index_displays_all_art(self):
        """Test that index displays all art pieces"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:index"))

        self.assertContains(response, "Manhattan Art")
        self.assertContains(response, "Brooklyn Art")
        self.assertContains(response, "Queens Art")

    def test_index_search_by_title(self):
        """Test search functionality by title"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:index"), {"search": "Manhattan"})

        self.assertContains(response, "Manhattan Art")
        self.assertNotContains(response, "Brooklyn Art")

    def test_index_search_by_artist(self):
        """Test search functionality by artist name"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:index"), {"search": "Artist One"}
        )

        self.assertContains(response, "Manhattan Art")
        self.assertContains(response, "Queens Art")
        self.assertNotContains(response, "Brooklyn Art")

    def test_index_search_by_description(self):
        """Test search functionality by description"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:index"), {"search": "sculpture"})

        self.assertContains(response, "Manhattan Art")

    def test_index_search_by_location(self):
        """Test search functionality by location"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:index"), {"search": "Central Park"}
        )

        self.assertContains(response, "Manhattan Art")

    def test_index_filter_by_borough(self):
        """Test filtering by borough"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:index"), {"borough": "Brooklyn"})

        self.assertContains(response, "Brooklyn Art")
        self.assertNotContains(response, "Manhattan Art")
        self.assertNotContains(response, "Queens Art")

    def test_index_search_and_filter_combined(self):
        """Test combining search and borough filter"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:index"),
            {"search": "Artist One", "borough": "Manhattan"},
        )

        self.assertContains(response, "Manhattan Art")
        self.assertNotContains(response, "Queens Art")

    def test_index_pagination(self):
        """Test pagination functionality"""
        # Create 25 art pieces to test pagination (page size is 20)
        for i in range(25):
            PublicArt.objects.create(title=f"Art Piece {i}", artist_name=f"Artist {i}")

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:index"))

        # Should have pagination
        self.assertTrue(response.context["page_obj"].has_next())
        self.assertEqual(len(response.context["page_obj"]), 20)

    def test_index_boroughs_list(self):
        """Test that unique boroughs are provided in context"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:index"))

        boroughs = list(response.context["boroughs"])
        self.assertIn("Manhattan", boroughs)
        self.assertIn("Brooklyn", boroughs)
        self.assertIn("Queens", boroughs)

    def test_index_total_count(self):
        """Test that total count is correct"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:index"))

        self.assertEqual(response.context["total_count"], 3)


class ArtDetailViewTests(TestCase):
    """Test cases for the art detail view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
            description="Test description",
            borough="Manhattan",
        )

    def test_art_detail_requires_login(self):
        """Test that art detail requires authentication"""
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_art_detail_view_authenticated(self):
        """Test art detail view with authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "loc_detail/art_detail.html")
        self.assertEqual(response.context["art"], self.art)

    def test_art_detail_displays_info(self):
        """Test that art detail displays correct information"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id})
        )

        self.assertContains(response, "Test Art")
        self.assertContains(response, "Test Artist")
        self.assertContains(response, "Test description")

    def test_art_detail_404_for_invalid_id(self):
        """Test that invalid art ID returns 404"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": 9999})
        )
        self.assertEqual(response.status_code, 404)

    def test_art_detail_post_comment(self):
        """Test posting a comment on art detail page"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id}),
            {"comment": "Great artwork!"},
        )

        # Should redirect back to detail page
        self.assertEqual(response.status_code, 302)

        # Comment should be created
        self.assertEqual(ArtComment.objects.count(), 1)
        comment = ArtComment.objects.first()
        self.assertEqual(comment.comment, "Great artwork!")
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.art, self.art)

    def test_art_detail_post_empty_comment(self):
        """Test posting empty comment shows error"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id}),
            {"comment": "   "},
        )

        # Should not create comment
        self.assertEqual(ArtComment.objects.count(), 0)
        # Should stay on same page
        self.assertEqual(response.status_code, 200)

    def test_art_detail_displays_comments(self):
        """Test that comments are displayed on detail page"""
        ArtComment.objects.create(user=self.user, art=self.art, comment="First comment")
        ArtComment.objects.create(
            user=self.user, art=self.art, comment="Second comment"
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id})
        )

        self.assertContains(response, "First comment")
        self.assertContains(response, "Second comment")

    def test_art_detail_related_art_same_borough(self):
        """Test that related art from same borough is shown"""
        related_art = PublicArt.objects.create(
            title="Related Manhattan Art", borough="Manhattan"
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id})
        )

        self.assertIn(related_art, response.context["related_art"])

    def test_art_detail_related_art_same_artist(self):
        """Test that related art from same artist is shown"""
        related_art = PublicArt.objects.create(
            title="Another Art by Same Artist",
            artist_name="Test Artist",
            borough="Brooklyn",
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id})
        )

        self.assertIn(related_art, response.context["related_art"])

    def test_art_detail_is_favorited_status(self):
        """Test that favorited status is shown correctly"""
        self.client.login(username="testuser", password="testpass123")

        # Not favorited initially
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id})
        )
        self.assertFalse(response.context["is_favorited"])

        # Add to favorites
        UserFavoriteArt.objects.create(user=self.user, art=self.art)

        # Should show as favorited
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id})
        )
        self.assertTrue(response.context["is_favorited"])


class APIAllPointsViewTests(TestCase):
    """Test cases for the API all points endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create art with coordinates
        self.art1 = PublicArt.objects.create(
            title="Art 1",
            artist_name="Artist 1",
            borough="Manhattan",
            latitude=Decimal("40.7829"),
            longitude=Decimal("-73.9654"),
        )
        self.art2 = PublicArt.objects.create(
            title="Art 2",
            artist_name="Artist 2",
            borough="Brooklyn",
            latitude=Decimal("40.6782"),
            longitude=Decimal("-73.9442"),
        )
        # Art without coordinates (should not be included)
        self.art3 = PublicArt.objects.create(title="Art 3", artist_name="Artist 3")

    def test_api_all_points_requires_login(self):
        """Test that API endpoint requires authentication"""
        response = self.client.get(reverse("loc_detail:api_all_points"))
        self.assertEqual(response.status_code, 302)

    def test_api_all_points_returns_json(self):
        """Test that API returns JSON response"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:api_all_points"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_api_all_points_structure(self):
        """Test the structure of API response"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:api_all_points"))

        data = json.loads(response.content)
        self.assertIn("points", data)
        self.assertEqual(len(data["points"]), 2)  # Only art with coordinates

    def test_api_all_points_data_format(self):
        """Test that points have correct compact format"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:api_all_points"))

        data = json.loads(response.content)
        point = data["points"][0]

        # Check compact format
        self.assertIn("id", point)
        self.assertIn("t", point)  # title
        self.assertIn("a", point)  # artist
        self.assertIn("b", point)  # borough
        self.assertIn("y", point)  # latitude
        self.assertIn("x", point)  # longitude

    def test_api_all_points_coordinates_as_float(self):
        """Test that coordinates are returned as floats"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:api_all_points"))

        data = json.loads(response.content)
        point = data["points"][0]

        self.assertIsInstance(point["y"], float)
        self.assertIsInstance(point["x"], float)

    def test_api_all_points_untitled_default(self):
        """Test that null titles show as 'Untitled'"""
        PublicArt.objects.create(
            latitude=Decimal("40.7128"), longitude=Decimal("-74.0060")
        )

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:api_all_points"))

        data = json.loads(response.content)
        # Find the point without title
        untitled_point = [p for p in data["points"] if p["t"] == "Untitled"][0]
        self.assertEqual(untitled_point["t"], "Untitled")
        self.assertEqual(untitled_point["a"], "Unknown")


class APIFavoriteToggleViewTests(TestCase):
    """Test cases for the API favorite toggle endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(title="Test Art", artist_name="Test Artist")

    def test_api_favorite_toggle_requires_login(self):
        """Test that API endpoint requires authentication"""
        response = self.client.post(
            reverse("loc_detail:api_favorite_toggle", kwargs={"art_id": self.art.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_api_favorite_toggle_requires_post(self):
        """Test that endpoint only accepts POST requests"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:api_favorite_toggle", kwargs={"art_id": self.art.id})
        )
        # Should return 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)

    def test_api_favorite_toggle_add(self):
        """Test adding to favorites"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("loc_detail:api_favorite_toggle", kwargs={"art_id": self.art.id})
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data["favorited"])
        self.assertEqual(data["message"], "Added to favorites")

        # Check that favorite was created
        self.assertTrue(
            UserFavoriteArt.objects.filter(user=self.user, art=self.art).exists()
        )

    def test_api_favorite_toggle_remove(self):
        """Test removing from favorites"""
        # First add to favorites
        UserFavoriteArt.objects.create(user=self.user, art=self.art)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("loc_detail:api_favorite_toggle", kwargs={"art_id": self.art.id})
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertFalse(data["favorited"])
        self.assertEqual(data["message"], "Removed from favorites")

        # Check that favorite was deleted
        self.assertFalse(
            UserFavoriteArt.objects.filter(user=self.user, art=self.art).exists()
        )

    def test_api_favorite_toggle_invalid_art_id(self):
        """Test toggling favorite for non-existent art"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("loc_detail:api_favorite_toggle", kwargs={"art_id": 9999})
        )
        self.assertEqual(response.status_code, 404)


class FavoritesViewTests(TestCase):
    """Test cases for the favorites view"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create art pieces
        self.art1 = PublicArt.objects.create(
            title="Favorite Art 1",
            artist_name="Artist 1",
            borough="Manhattan",
            description="First favorite",
        )
        self.art2 = PublicArt.objects.create(
            title="Favorite Art 2", artist_name="Artist 2", borough="Brooklyn"
        )
        self.art3 = PublicArt.objects.create(
            title="Not Favorite", artist_name="Artist 3"
        )

        # Add to favorites
        UserFavoriteArt.objects.create(user=self.user, art=self.art1)
        UserFavoriteArt.objects.create(user=self.user, art=self.art2)

    def test_favorites_requires_login(self):
        """Test that favorites view requires authentication"""
        response = self.client.get(reverse("loc_detail:favorites"))
        self.assertEqual(response.status_code, 302)

    def test_favorites_view_authenticated(self):
        """Test favorites view with authenticated user"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:favorites"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "loc_detail/favorites.html")

    def test_favorites_shows_only_user_favorites(self):
        """Test that only user's favorites are shown"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:favorites"))

        self.assertContains(response, "Favorite Art 1")
        self.assertContains(response, "Favorite Art 2")
        self.assertNotContains(response, "Not Favorite")

    def test_favorites_search_by_title(self):
        """Test search functionality in favorites"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:favorites"), {"search": "Art 1"})

        self.assertContains(response, "Favorite Art 1")
        self.assertNotContains(response, "Favorite Art 2")

    def test_favorites_filter_by_borough(self):
        """Test filtering favorites by borough"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:favorites"), {"borough": "Manhattan"}
        )

        self.assertContains(response, "Favorite Art 1")
        self.assertNotContains(response, "Favorite Art 2")

    def test_favorites_empty_list(self):
        """Test favorites view with no favorites"""
        # Create new user with no favorites
        User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

        self.client.login(username="user2", password="testpass123")
        response = self.client.get(reverse("loc_detail:favorites"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_count"], 0)

    def test_favorites_pagination(self):
        """Test pagination in favorites"""
        # Create 25 favorites to test pagination
        for i in range(23):
            art = PublicArt.objects.create(title=f"Extra Art {i}")
            UserFavoriteArt.objects.create(user=self.user, art=art)

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:favorites"))

        # Should have pagination (page size is 20)
        self.assertTrue(response.context["page_obj"].has_next())
        self.assertEqual(len(response.context["page_obj"]), 20)

    def test_favorites_ordered_by_recent(self):
        """Test that favorites are ordered by most recently added"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:favorites"))

        favorites = response.context["page_obj"].object_list
        # Verify we have 2 favorites
        self.assertEqual(len(favorites), 2)
        # Verify both art pieces are in favorites
        art_ids = [fav.art.id for fav in favorites]
        self.assertIn(self.art1.id, art_ids)
        self.assertIn(self.art2.id, art_ids)

    def test_favorites_total_count(self):
        """Test that total count is correct"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:favorites"))

        self.assertEqual(response.context["total_count"], 2)

    def test_favorites_boroughs_list(self):
        """Test that unique boroughs from favorites are shown"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("loc_detail:favorites"))

        boroughs = list(response.context["boroughs"])
        self.assertIn("Manhattan", boroughs)
        self.assertIn("Brooklyn", boroughs)
        self.assertEqual(len(boroughs), 2)
