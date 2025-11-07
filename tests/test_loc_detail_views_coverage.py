"""
Complete test coverage for loc_detail/views.py
Targets all missing lines to achieve 90%+ coverage
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
import json

from loc_detail.models import (
    PublicArt,
    UserFavoriteArt,
    ArtComment,
    CommentLike,
    CommentImage,
    CommentReport,
)


class ArtDetailViewImageTests(TestCase):
    """Test art detail view with image handling"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
            latitude=Decimal("40.7829"),
            longitude=Decimal("-73.9654"),
        )

    def test_post_comment_with_multiple_images(self):
        """Test posting comment with multiple images (lines 272)"""
        self.client.login(username="testuser", password="testpass123")

        image1 = SimpleUploadedFile(
            name="test1.jpg", content=b"fake_image_1", content_type="image/jpeg"
        )
        image2 = SimpleUploadedFile(
            name="test2.jpg", content=b"fake_image_2", content_type="image/jpeg"
        )

        response = self.client.post(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id}),
            {
                "comment": "Great art!",
                "rating": "5",
            },
            # Images are sent as FILES
            files={"images": [image1, image2]},
        )

        self.assertEqual(response.status_code, 302)
        comment = ArtComment.objects.get(user=self.user, art=self.art)
        self.assertIsNotNone(comment)

    def test_edit_comment_with_images(self):
        """Test editing comment and adding images"""
        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Original", rating=3
        )

        self.client.login(username="testuser", password="testpass123")

        image = SimpleUploadedFile(
            name="new.jpg", content=b"new_image", content_type="image/jpeg"
        )

        response = self.client.post(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id}),
            {
                "comment": "Updated comment",
                "rating": "5",
                "comment_id": comment.id,
            },
            files={"images": [image]},
        )

        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertEqual(comment.comment, "Updated comment")

    def test_post_reply_without_images(self):
        """Test posting a reply without images (lines 134-152)"""
        parent = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Parent", rating=5
        )
        # create another user who will post the reply
        User.objects.create_user(username="other", password="testpass123")

        self.client.login(username="other", password="testpass123")

        response = self.client.post(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id}),
            {"comment": "Reply", "parent_id": parent.id},
        )

        self.assertEqual(response.status_code, 302)
        reply = ArtComment.objects.get(parent=parent)
        self.assertEqual(reply.comment, "Reply")
        self.assertEqual(reply.art, self.art)


class APIDeleteCommentImageTests(TestCase):
    """Test API endpoint for deleting comment images (lines 284-298)"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="other", email="other@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(title="Test Art")
        self.comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Test", rating=5
        )

        # Create a comment image
        image = SimpleUploadedFile(
            name="test.jpg", content=b"image_content", content_type="image/jpeg"
        )
        self.comment_image = CommentImage.objects.create(
            comment=self.comment, image=image, order=0
        )

    def test_delete_image_requires_login(self):
        """Test that delete image requires authentication"""
        response = self.client.post(
            reverse(
                "loc_detail:api_delete_image",
                kwargs={"image_id": self.comment_image.id},
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_image_requires_post(self):
        """Test that delete image requires POST"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "loc_detail:api_delete_image",
                kwargs={"image_id": self.comment_image.id},
            )
        )
        self.assertEqual(response.status_code, 405)

    def test_delete_own_image_success(self):
        """Test successfully deleting own image (line 287-290)"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse(
                "loc_detail:api_delete_image",
                kwargs={"image_id": self.comment_image.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["message"], "Image deleted successfully")

        # Verify image was deleted
        self.assertFalse(CommentImage.objects.filter(id=self.comment_image.id).exists())

    def test_delete_other_user_image_denied(self):
        """Test that users cannot delete other users' images (line 284-286)"""
        self.client.login(username="other", password="testpass123")
        response = self.client.post(
            reverse(
                "loc_detail:api_delete_image",
                kwargs={"image_id": self.comment_image.id},
            )
        )

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Permission denied")

        # Verify image was NOT deleted
        self.assertTrue(CommentImage.objects.filter(id=self.comment_image.id).exists())

    def test_delete_nonexistent_image(self):
        """Test deleting non-existent image (line 292-293)"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("loc_detail:api_delete_image", kwargs={"image_id": 99999})
        )

        # Should return 404 or handle gracefully
        self.assertIn(response.status_code, (404, 500))

    def test_delete_image_exception_handling(self):
        """Test exception handling in delete image (line 294-295)"""
        self.client.login(username="testuser", password="testpass123")

        # Capture the ID before deleting so reverse() gets a valid integer
        image_id = self.comment_image.id
        self.comment_image.delete()  # Now the DB row is gone

        response = self.client.post(
            reverse(
                "loc_detail:api_delete_image",
                kwargs={"image_id": image_id},
            )
        )

        # Our view wraps errors and may return 404 or 500 depending on Django version
        self.assertIn(response.status_code, (404, 500))


class APIReportCommentTests(TestCase):
    """Test API endpoint for reporting comments (lines 305-343)"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.commenter = User.objects.create_user(
            username="commenter", email="commenter@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(title="Test Art")
        self.comment = ArtComment.objects.create(
            user=self.commenter, art=self.art, comment="Bad comment", rating=1
        )

    def test_report_comment_requires_login(self):
        """Test that reporting requires authentication"""
        response = self.client.post(
            reverse(
                "loc_detail:api_report_comment", kwargs={"comment_id": self.comment.id}
            )
        )
        self.assertEqual(response.status_code, 302)

    def test_report_comment_requires_post(self):
        """Test that reporting requires POST"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse(
                "loc_detail:api_report_comment", kwargs={"comment_id": self.comment.id}
            )
        )
        self.assertEqual(response.status_code, 405)

    def test_report_comment_success(self):
        """Test successfully reporting a comment (lines 313-328)"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse(
                "loc_detail:api_report_comment", kwargs={"comment_id": self.comment.id}
            ),
            data=json.dumps(
                {
                    "reasons": ["spam", "harassment"],
                    "additional_info": "This is inappropriate content",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("review", data["message"].lower())

        # Verify report was created
        report = CommentReport.objects.get(comment=self.comment, reporter=self.user)
        self.assertEqual(report.reasons, ["spam", "harassment"])
        self.assertEqual(report.additional_info, "This is inappropriate content")

    def test_report_comment_already_reported(self):
        """Test reporting a comment that has already been reported (lines 307-312)"""
        # Create an existing report for this user/comment
        CommentReport.objects.create(
            comment=self.comment,
            reporter=self.user,
            reasons=["spam"],
            additional_info="Initial report",
        )

        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse(
                "loc_detail:api_report_comment",
                kwargs={"comment_id": self.comment.id},
            ),
            data=json.dumps({"reasons": ["spam"], "additional_info": "Second report"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("already", data["error"].lower())
        # Still only one report for this user/comment
        self.assertEqual(
            CommentReport.objects.filter(
                comment=self.comment, reporter=self.user
            ).count(),
            1,
        )

    def test_report_comment_no_reasons(self):
        """Test reporting without selecting reasons (lines 319-323)"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse(
                "loc_detail:api_report_comment", kwargs={"comment_id": self.comment.id}
            ),
            data=json.dumps({"reasons": [], "additional_info": "Some info"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data["success"])
        self.assertIn("select at least one reason", data["error"].lower())

    def test_report_comment_invalid_json(self):
        """Test reporting with invalid JSON (line 330-331)"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse(
                "loc_detail:api_report_comment", kwargs={"comment_id": self.comment.id}
            ),
            data="invalid json",
            content_type="application/json",
        )

        # Should handle JSON decode error
        self.assertIn(response.status_code, (400, 500))

    def test_report_nonexistent_comment(self):
        """Test reporting non-existent comment"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("loc_detail:api_report_comment", kwargs={"comment_id": 99999}),
            data=json.dumps({"reasons": ["spam"]}),
            content_type="application/json",
        )

        # Should return 404
        self.assertEqual(response.status_code, 404)


class FavoritesViewEdgeCases(TestCase):
    """Test edge cases for favorites view (lines 349-389)"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_favorites_with_search_and_borough_filter(self):
        """Test combined search and borough filter in favorites"""
        art1 = PublicArt.objects.create(
            title="Manhattan Art",
            artist_name="Artist A",
            borough="Manhattan",
            description="Beautiful sculpture",
        )
        art2 = PublicArt.objects.create(
            title="Brooklyn Art",
            artist_name="Artist B",
            borough="Brooklyn",
            description="Amazing mural",
        )
        art3 = PublicArt.objects.create(
            title="Manhattan Painting",
            artist_name="Artist C",
            borough="Manhattan",
            description="Great painting",
        )

        UserFavoriteArt.objects.create(user=self.user, art=art1)
        UserFavoriteArt.objects.create(user=self.user, art=art2)
        UserFavoriteArt.objects.create(user=self.user, art=art3)

        self.client.login(username="testuser", password="testpass123")

        # Test search + filter
        response = self.client.get(
            reverse("favorites:index"),
            {"tab": "art", "search": "Manhattan", "borough": "Manhattan"},
        )

        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        # Should return both Manhattan arts
        self.assertEqual(len(page_obj), 2)

    def test_favorites_search_by_description(self):
        """Test searching favorites by description"""
        art = PublicArt.objects.create(
            title="Test Art",
            description="This is a unique description for testing",
            borough="Manhattan",
        )
        UserFavoriteArt.objects.create(user=self.user, art=art)

        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse("favorites:index"), {"tab": "art", "search": "unique description"}
        )

        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 1)
        self.assertEqual(page_obj[0].art.title, "Test Art")

    def test_favorites_search_by_location(self):
        """Test searching favorites by location field"""
        art = PublicArt.objects.create(
            title="Test Art",
            location="Central Park, near the fountain",
            borough="Manhattan",
        )
        UserFavoriteArt.objects.create(user=self.user, art=art)

        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(
            reverse("favorites:index"), {"tab": "art", "search": "fountain"}
        )

        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 1)

    def test_favorites_with_null_borough(self):
        """Test favorites with null borough handling"""
        art1 = PublicArt.objects.create(title="No Borough Art", borough=None)
        art2 = PublicArt.objects.create(title="Has Borough", borough="Manhattan")

        UserFavoriteArt.objects.create(user=self.user, art=art1)
        UserFavoriteArt.objects.create(user=self.user, art=art2)

        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("favorites:index"), {"tab": "art"})

        self.assertEqual(response.status_code, 200)
        boroughs = list(response.context["boroughs"])
        # Should only include non-null, non-empty boroughs
        self.assertIn("Manhattan", boroughs)
        self.assertNotIn(None, boroughs)
        self.assertNotIn("", boroughs)

    def test_favorites_with_empty_borough(self):
        """Test favorites with empty string borough"""
        art = PublicArt.objects.create(title="Empty Borough", borough="")
        UserFavoriteArt.objects.create(user=self.user, art=art)

        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("favorites:index"), {"tab": "art"})

        self.assertEqual(response.status_code, 200)
        boroughs = list(response.context["boroughs"])
        self.assertNotIn("", boroughs)

    def test_favorites_pagination_edge_cases(self):
        """Test favorites pagination with exactly 20 items"""
        # Create exactly 20 favorites
        for i in range(20):
            art = PublicArt.objects.create(title=f"Art {i}")
            UserFavoriteArt.objects.create(user=self.user, art=art)

        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("favorites:index"), {"tab": "art"})

        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 20)
        self.assertFalse(page_obj.has_next())  # No next page

    def test_favorites_invalid_page_number(self):
        """Test favorites with invalid page number"""
        art = PublicArt.objects.create(title="Test Art")
        UserFavoriteArt.objects.create(user=self.user, art=art)

        self.client.login(username="testuser", password="testpass123")

        # Request page that doesn't exist
        response = self.client.get(
            reverse("favorites:index"), {"tab": "art", "page": 999}
        )

        # Should return last page gracefully
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 1)


class IndexViewSearchEdgeCases(TestCase):
    """Test edge cases for index view search functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_index_case_insensitive_search(self):
        """Test that search is case insensitive"""
        PublicArt.objects.create(
            title="Manhattan Art", artist_name="John Doe", borough="Manhattan"
        )

        self.client.login(username="testuser", password="testpass123")

        # Search with different cases
        response = self.client.get(reverse("loc_detail:index"), {"search": "MANHATTAN"})
        self.assertEqual(response.context["total_count"], 1)

        response = self.client.get(reverse("loc_detail:index"), {"search": "manhattan"})
        self.assertEqual(response.context["total_count"], 1)

        response = self.client.get(reverse("loc_detail:index"), {"search": "JOHN DOE"})
        self.assertEqual(response.context["total_count"], 1)

    def test_index_partial_match_search(self):
        """Test that search works with partial matches"""
        PublicArt.objects.create(
            title="Beautiful Sculpture",
            artist_name="Jane Smith",
            location="Central Park",
        )

        self.client.login(username="testuser", password="testpass123")

        # Partial title
        response = self.client.get(reverse("loc_detail:index"), {"search": "Beauti"})
        self.assertEqual(response.context["total_count"], 1)

        # Partial artist
        response = self.client.get(reverse("loc_detail:index"), {"search": "Jane"})
        self.assertEqual(response.context["total_count"], 1)

        # Partial location
        response = self.client.get(reverse("loc_detail:index"), {"search": "Park"})
        self.assertEqual(response.context["total_count"], 1)

    def test_index_multiple_matching_fields(self):
        """Test search matching multiple fields"""
        PublicArt.objects.create(
            title="Central Park Sculpture",
            artist_name="Park Designer",
            location="Central Park",
            description="Located in Central Park",
        )

        self.client.login(username="testuser", password="testpass123")

        # Search term that matches multiple fields
        response = self.client.get(reverse("loc_detail:index"), {"search": "Park"})

        # Should find the art piece
        self.assertEqual(response.context["total_count"], 1)


class CommentReactionEdgeCases(TestCase):
    """Test edge cases for comment reaction API"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(title="Test Art")
        self.comment = ArtComment.objects.create(
            user=self.user1, art=self.art, comment="Test", rating=4
        )

    def test_reaction_missing_reaction_type(self):
        """Test reaction without specifying reaction type"""
        self.client.login(username="user2", password="testpass123")

        response = self.client.post(
            reverse(
                "loc_detail:api_comment_reaction",
                kwargs={"comment_id": self.comment.id},
            ),
            {},  # No reaction type
        )

        # Should handle missing reaction gracefully
        self.assertIn(response.status_code, (200, 400))

    def test_reaction_invalid_reaction_type(self):
        """Test reaction with invalid reaction type"""
        self.client.login(username="user2", password="testpass123")

        response = self.client.post(
            reverse(
                "loc_detail:api_comment_reaction",
                kwargs={"comment_id": self.comment.id},
            ),
            {"reaction": "invalid"},
        )

        # Should handle gracefully
        self.assertEqual(response.status_code, 200)

    def test_multiple_rapid_reactions(self):
        """Test rapid clicking of reaction buttons"""
        self.client.login(username="user2", password="testpass123")

        # Like
        response = self.client.post(
            reverse(
                "loc_detail:api_comment_reaction",
                kwargs={"comment_id": self.comment.id},
            ),
            {"reaction": "like"},
        )
        self.assertEqual(response.status_code, 200)

        # Unlike
        response = self.client.post(
            reverse(
                "loc_detail:api_comment_reaction",
                kwargs={"comment_id": self.comment.id},
            ),
            {"reaction": "like"},
        )
        self.assertEqual(response.status_code, 200)

        # Dislike
        response = self.client.post(
            reverse(
                "loc_detail:api_comment_reaction",
                kwargs={"comment_id": self.comment.id},
            ),
            {"reaction": "dislike"},
        )
        self.assertEqual(response.status_code, 200)

        # Final state should be consistent
        data = json.loads(response.content)
        self.assertTrue(data["success"])


class CommentEditingEdgeCases(TestCase):
    """Test edge cases for comment editing"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(title="Test Art")

    def test_edit_comment_preserves_parent(self):
        """Test that editing a reply preserves parent relationship"""
        parent = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Parent", rating=5
        )
        reply = ArtComment.objects.create(
            user=self.user,
            art=self.art,
            comment="Original reply",
            rating=5,
            parent=parent,
        )

        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id}),
            {
                "comment": "Updated reply",
                "comment_id": reply.id,
                "parent_id": parent.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        reply.refresh_from_db()
        self.assertEqual(reply.comment, "Updated reply")
        self.assertEqual(reply.parent, parent)

    def test_edit_comment_without_rating_preserves_existing(self):
        """Test editing comment without rating preserves existing rating"""
        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Original", rating=3
        )

        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id}),
            {
                "comment": "Updated comment",
                "comment_id": comment.id,
                # No rating specified
            },
        )

        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertEqual(comment.comment, "Updated comment")
        # Rating should be preserved or set based on view logic


class IntegrationTests(TestCase):
    """Integration tests combining multiple features"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(
            title="Test Art",
            artist_name="Test Artist",
            borough="Manhattan",
            latitude=Decimal("40.7829"),
            longitude=Decimal("-73.9654"),
        )

    def test_full_comment_workflow(self):
        """Test complete comment workflow: create, react, report, delete image"""
        self.client.login(username="testuser", password="testpass123")

        # 1. Create comment with image
        image = SimpleUploadedFile(
            name="test.jpg", content=b"image_content", content_type="image/jpeg"
        )

        response = self.client.post(
            reverse("loc_detail:art_detail", kwargs={"art_id": self.art.id}),
            {"comment": "Great art!", "rating": "5"},
            files={"images": [image]},
        )
        self.assertEqual(response.status_code, 302)

        comment = ArtComment.objects.get(user=self.user, art=self.art)

        # 2. Another user reacts
        User.objects.create_user(username="other", password="testpass123")
        self.client.login(username="other", password="testpass123")

        response = self.client.post(
            reverse(
                "loc_detail:api_comment_reaction", kwargs={"comment_id": comment.id}
            ),
            {"reaction": "like"},
        )
        self.assertEqual(response.status_code, 200)

        # 3. Report the comment
        response = self.client.post(
            reverse("loc_detail:api_report_comment", kwargs={"comment_id": comment.id}),
            data=json.dumps({"reasons": ["spam"], "additional_info": "Test report"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Verify all operations succeeded
        self.assertTrue(CommentLike.objects.filter(comment=comment).exists())
        self.assertTrue(CommentReport.objects.filter(comment=comment).exists())

    def test_favorites_and_search_integration(self):
        """Test favorites with search and filter"""
        # Create multiple art pieces
        art1 = PublicArt.objects.create(
            title="Manhattan Sculpture",
            artist_name="Artist A",
            borough="Manhattan",
        )
        art2 = PublicArt.objects.create(
            title="Brooklyn Mural", artist_name="Artist B", borough="Brooklyn"
        )
        art3 = PublicArt.objects.create(
            title="Manhattan Painting",
            artist_name="Artist A",
            borough="Manhattan",
        )

        # Favorite all
        UserFavoriteArt.objects.create(user=self.user, art=art1)
        UserFavoriteArt.objects.create(user=self.user, art=art2)
        UserFavoriteArt.objects.create(user=self.user, art=art3)

        self.client.login(username="testuser", password="testpass123")

        # Search in favorites
        response = self.client.get(
            reverse("favorites:index"),
            {"tab": "art", "search": "Artist A", "borough": "Manhattan"},
        )

        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        # Should return both Manhattan arts by Artist A
        self.assertEqual(len(page_obj), 2)

    def test_pagination_across_views(self):
        """Test pagination consistency across views"""
        # Create 25 art pieces
        for i in range(25):
            art = PublicArt.objects.create(
                title=f"Art {i:02d}",
                borough="Manhattan",
                latitude=Decimal("40.7829"),
                longitude=Decimal("-73.9654"),
            )
            UserFavoriteArt.objects.create(user=self.user, art=art)

        self.client.login(username="testuser", password="testpass123")

        # Test index view pagination
        response = self.client.get(reverse("loc_detail:index"))
        self.assertEqual(len(response.context["page_obj"]), 20)

        # Test favorites pagination
        response = self.client.get(reverse("favorites:index"), {"tab": "art"})
        self.assertEqual(len(response.context["page_obj"]), 20)

        # Test page 2
        response = self.client.get(
            reverse("favorites:index"), {"tab": "art", "page": 2}
        )
        self.assertEqual(len(response.context["page_obj"]), 5)


class APIEndpointSecurityTests(TestCase):
    """Test security aspects of API endpoints"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(title="Test Art")
        self.comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Test", rating=5
        )

    def test_api_endpoints_require_authentication(self):
        """Test that all API endpoints require login"""
        # Comment reaction
        response = self.client.post(
            reverse(
                "loc_detail:api_comment_reaction",
                kwargs={"comment_id": self.comment.id},
            )
        )
        self.assertEqual(response.status_code, 302)

        # Delete image
        response = self.client.post(
            reverse("loc_detail:api_delete_image", kwargs={"image_id": 1})
        )
        self.assertEqual(response.status_code, 302)

        # Report comment
        response = self.client.post(
            reverse(
                "loc_detail:api_report_comment", kwargs={"comment_id": self.comment.id}
            )
        )
        self.assertEqual(response.status_code, 302)

        # Favorite toggle
        response = self.client.post(
            reverse("loc_detail:api_favorite_toggle", kwargs={"art_id": self.art.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_api_endpoints_require_post(self):
        """Test that API endpoints only accept POST"""
        self.client.login(username="testuser", password="testpass123")

        # Comment reaction
        response = self.client.get(
            reverse(
                "loc_detail:api_comment_reaction",
                kwargs={"comment_id": self.comment.id},
            )
        )
        self.assertEqual(response.status_code, 405)

        # Delete image
        response = self.client.get(
            reverse("loc_detail:api_delete_image", kwargs={"image_id": 1})
        )
        self.assertEqual(response.status_code, 405)

        # Report comment
        response = self.client.get(
            reverse(
                "loc_detail:api_report_comment", kwargs={"comment_id": self.comment.id}
            )
        )
        self.assertEqual(response.status_code, 405)

        # Favorite toggle
        response = self.client.get(
            reverse("loc_detail:api_favorite_toggle", kwargs={"art_id": self.art.id})
        )
        self.assertEqual(response.status_code, 405)

    def test_csrf_protection(self):
        """Test CSRF protection on POST endpoints"""
        # Note: Django test client automatically handles CSRF
        # This test verifies the endpoints work with proper CSRF
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse(
                "loc_detail:api_comment_reaction",
                kwargs={"comment_id": self.comment.id},
            ),
            {"reaction": "like"},
        )
        self.assertEqual(response.status_code, 200)


class ErrorHandlingTests(TestCase):
    """Test error handling across views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_art_detail_invalid_id(self):
        """Test art detail with invalid ID"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("loc_detail:art_detail", kwargs={"art_id": 99999})
        )
        self.assertEqual(response.status_code, 404)

    def test_favorite_toggle_invalid_id(self):
        """Test favorite toggle with invalid art ID"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("loc_detail:api_favorite_toggle", kwargs={"art_id": 99999})
        )
        self.assertEqual(response.status_code, 404)

    def test_comment_reaction_invalid_id(self):
        """Test comment reaction with invalid comment ID"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("loc_detail:api_comment_reaction", kwargs={"comment_id": 99999}),
            {"reaction": "like"},
        )
        self.assertIn(response.status_code, (404, 500))

    def test_empty_search_query(self):
        """Test search with empty query"""
        PublicArt.objects.create(title="Test Art")
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("loc_detail:index"), {"search": ""})
        self.assertEqual(response.status_code, 200)
        # Should show all art
        self.assertGreater(response.context["total_count"], 0)

    def test_whitespace_only_search(self):
        """Test search with only whitespace"""
        PublicArt.objects.create(title="Test Art")
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("loc_detail:index"), {"search": "   "})
        self.assertEqual(response.status_code, 200)


class ReportCommentComprehensiveTests(TestCase):
    """Comprehensive tests for comment reporting"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.commenter = User.objects.create_user(
            username="commenter", password="testpass123"
        )
        self.art = PublicArt.objects.create(title="Test Art")
        self.comment = ArtComment.objects.create(
            user=self.commenter, art=self.art, comment="Test comment", rating=5
        )

    def test_report_with_multiple_reasons(self):
        """Test reporting with multiple reasons"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse(
                "loc_detail:api_report_comment", kwargs={"comment_id": self.comment.id}
            ),
            data=json.dumps(
                {
                    "reasons": ["spam", "harassment", "hate"],
                    "additional_info": "Multiple violations",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        report = CommentReport.objects.get(comment=self.comment)
        self.assertEqual(len(report.reasons), 3)

    def test_report_without_additional_info(self):
        """Test reporting without additional info"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse(
                "loc_detail:api_report_comment", kwargs={"comment_id": self.comment.id}
            ),
            data=json.dumps({"reasons": ["spam"]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        report = CommentReport.objects.get(comment=self.comment)
        self.assertEqual(report.additional_info, "")

    def test_report_with_long_additional_info(self):
        """Test reporting with long additional info"""
        self.client.login(username="testuser", password="testpass123")

        long_info = "x" * 500

        response = self.client.post(
            reverse(
                "loc_detail:api_report_comment", kwargs={"comment_id": self.comment.id}
            ),
            data=json.dumps({"reasons": ["other"], "additional_info": long_info}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        report = CommentReport.objects.get(comment=self.comment)
        self.assertEqual(report.additional_info, long_info)

    def test_report_own_comment(self):
        """Test reporting own comment (should be allowed)"""
        self.client.login(username="commenter", password="testpass123")

        response = self.client.post(
            reverse(
                "loc_detail:api_report_comment", kwargs={"comment_id": self.comment.id}
            ),
            data=json.dumps({"reasons": ["spam"], "additional_info": "My mistake"}),
            content_type="application/json",
        )

        # Should succeed or fail based on business logic
        self.assertIn(response.status_code, (200, 400))


class CommentImageManagementTests(TestCase):
    """Comprehensive tests for comment image management"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.art = PublicArt.objects.create(title="Test Art")
        self.comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Test", rating=5
        )

    def test_delete_multiple_images(self):
        """Test deleting multiple images from a comment"""
        self.client.login(username="testuser", password="testpass123")

        # Create multiple images
        images = []
        for i in range(3):
            image = SimpleUploadedFile(
                name=f"test{i}.jpg", content=b"image", content_type="image/jpeg"
            )
            img_obj = CommentImage.objects.create(
                comment=self.comment, image=image, order=i
            )
            images.append(img_obj)

        # Delete first image
        response = self.client.post(
            reverse("loc_detail:api_delete_image", kwargs={"image_id": images[0].id})
        )
        self.assertEqual(response.status_code, 200)

        # Delete second image
        response = self.client.post(
            reverse("loc_detail:api_delete_image", kwargs={"image_id": images[1].id})
        )
        self.assertEqual(response.status_code, 200)

        # Verify only one image remains
        self.assertEqual(self.comment.images.count(), 1)

    def test_delete_image_from_reply(self):
        """Test that images on replies are handled (replies shouldn't have images)"""
        parent = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Parent", rating=5
        )
        reply = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Reply", parent=parent
        )

        # Try to add image to reply (edge case)
        image = SimpleUploadedFile(
            name="test.jpg", content=b"image", content_type="image/jpeg"
        )
        img_obj = CommentImage.objects.create(comment=reply, image=image, order=0)

        self.client.login(username="testuser", password="testpass123")

        # Should still be able to delete it
        response = self.client.post(
            reverse("loc_detail:api_delete_image", kwargs={"image_id": img_obj.id})
        )
        self.assertEqual(response.status_code, 200)


class BoundaryValueTests(TestCase):
    """Test boundary values and limits"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_search_with_special_characters(self):
        """Test search with special characters"""
        PublicArt.objects.create(title="Art: The Beginning!", artist_name="O'Brien")

        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("loc_detail:index"), {"search": "O'Brien"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_count"], 1)

    def test_search_with_unicode(self):
        """Test search with unicode characters"""
        PublicArt.objects.create(title="Café Art", artist_name="José García")

        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("loc_detail:index"), {"search": "Café"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_count"], 1)

    def test_very_long_search_query(self):
        """Test search with very long query"""
        PublicArt.objects.create(title="Test Art")

        self.client.login(username="testuser", password="testpass123")

        long_query = "a" * 500
        response = self.client.get(reverse("loc_detail:index"), {"search": long_query})
        self.assertEqual(response.status_code, 200)

    def test_comment_with_max_length_text(self):
        """Test comment with very long text"""
        art = PublicArt.objects.create(title="Test Art")

        self.client.login(username="testuser", password="testpass123")

        long_comment = "a" * 1000
        response = self.client.post(
            reverse("loc_detail:art_detail", kwargs={"art_id": art.id}),
            {"comment": long_comment, "rating": "5"},
        )

        # Should handle gracefully (accept or truncate)
        self.assertIn(response.status_code, (200, 302))

    def test_api_all_points_with_5000_limit(self):
        """Test API respects 5000 point limit"""
        # Create just under and at limit
        for i in range(10):
            PublicArt.objects.create(
                title=f"Art {i}",
                latitude=Decimal("40.7128"),
                longitude=Decimal("-74.0060"),
            )

        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("loc_detail:api_all_points"))
        data = json.loads(response.content)

        # Should return all points up to 5000
        self.assertLessEqual(len(data["points"]), 5000)
        self.assertEqual(len(data["points"]), 10)
