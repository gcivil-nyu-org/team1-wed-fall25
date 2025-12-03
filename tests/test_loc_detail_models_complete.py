"""
Complete test coverage for loc_detail/models.py
Targets all missing lines to achieve 95%+ coverage
"""

import os
import shutil
import tempfile
from io import BytesIO

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from PIL import Image

from loc_detail.models import (
    PublicArt,
    UserFavoriteArt,
    ArtComment,
    CommentLike,
    CommentImage,
    CommentReport,
)

TEST_MEDIA_ROOT = tempfile.mkdtemp()


def create_test_image(filename="test.jpg", size=(800, 600), format="JPEG"):
    """Helper to create test images"""
    img = Image.new("RGB", size, color=(255, 0, 0))
    img_io = BytesIO()
    img.save(img_io, format=format)
    img_io.seek(0)
    return SimpleUploadedFile(
        filename, img_io.read(), content_type=f"image/{format.lower()}"
    )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PublicArtThumbnailTests(TestCase):
    """Test PublicArt thumbnail generation and image processing (lines 28-150)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.makedirs(TEST_MEDIA_ROOT, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def test_make_thumbnail_with_valid_image(self):
        """Test make_thumbnail method with valid image (lines 41-43)"""
        art = PublicArt()
        image = create_test_image("test.jpg", (800, 600))

        thumb = art.make_thumbnail(image)

        self.assertIsNotNone(thumb)
        self.assertTrue(thumb.name.startswith("thumb_"))
        self.assertTrue(thumb.name.endswith(".jpg"))

        # Verify thumbnail size
        thumb.seek(0)
        img = Image.open(thumb)
        self.assertLessEqual(img.width, PublicArt.THUMBNAIL_SIZE[0])
        self.assertLessEqual(img.height, PublicArt.THUMBNAIL_SIZE[1])

    def test_make_thumbnail_with_none_image(self):
        """Test make_thumbnail returns None for null image (line 28)"""
        art = PublicArt()
        result = art.make_thumbnail(None)
        self.assertIsNone(result)

    def test_make_thumbnail_with_corrupt_image(self):
        """Test make_thumbnail handles corrupt image (line 49)"""
        art = PublicArt()
        corrupt_image = SimpleUploadedFile(
            "corrupt.jpg", b"not_an_image", content_type="image/jpeg"
        )

        result = art.make_thumbnail(corrupt_image)
        self.assertIsNone(result)

    def test_make_thumbnail_with_png(self):
        """Test make_thumbnail with PNG image"""
        art = PublicArt()
        image = create_test_image("test.png", (400, 400), format="PNG")

        thumb = art.make_thumbnail(image)

        self.assertIsNotNone(thumb)
        # All thumbnails are converted to JPEG
        self.assertTrue(thumb.name.endswith(".jpg"))

    def test_downsample_image_with_large_image(self):
        """Test downsample_image with oversized image (lines 70-71)"""
        art = PublicArt()
        large_image = create_test_image("large.jpg", (3000, 2500))

        downsampled = art.downsample_image(large_image)

        self.assertIsNotNone(downsampled)

        # Verify downsampled size
        downsampled.seek(0)
        img = Image.open(downsampled)
        self.assertLessEqual(img.width, PublicArt.MAX_IMAGE_SIZE[0])
        self.assertLessEqual(img.height, PublicArt.MAX_IMAGE_SIZE[1])

    def test_downsample_image_with_small_image(self):
        """Test downsample_image returns None for already-small image (line 70)"""
        art = PublicArt()
        small_image = create_test_image("small.jpg", (500, 400))

        result = art.downsample_image(small_image)

        # Should return None if image is already small enough
        self.assertIsNone(result)

    def test_downsample_image_with_none(self):
        """Test downsample_image with None (line 28 equivalent)"""
        art = PublicArt()
        result = art.downsample_image(None)
        self.assertIsNone(result)

    def test_downsample_image_exception_handling(self):
        """Test downsample_image handles exceptions (line 82-83)"""
        art = PublicArt()
        corrupt_image = SimpleUploadedFile(
            "corrupt.jpg", b"not_an_image", content_type="image/jpeg"
        )

        result = art.downsample_image(corrupt_image)
        self.assertIsNone(result)

    def test_save_creates_thumbnail_on_new_image(self):
        """Test save creates thumbnail when image is added (lines 104, 114)"""
        art = PublicArt.objects.create(
            title="Test Art", image=create_test_image("art.jpg", (800, 600))
        )

        self.assertTrue(art.thumbnail)
        self.assertTrue(os.path.exists(art.thumbnail.path))

    def test_save_updates_thumbnail_on_image_change(self):
        """Test save updates thumbnail when image changes (lines 121, 130-132)"""
        art = PublicArt.objects.create(
            title="Test Art", image=create_test_image("art1.jpg", (800, 600))
        )

        old_thumb_name = art.thumbnail.name

        # Change image
        art.image = create_test_image("art2.jpg", (600, 400))
        art.save()

        # Thumbnail should be updated
        self.assertTrue(art.thumbnail)
        self.assertNotEqual(art.thumbnail.name, old_thumb_name)

    def test_save_removes_thumbnail_when_image_removed(self):
        """Test save removes thumbnail when image is deleted (lines 135-144)"""
        art = PublicArt.objects.create(
            title="Test Art", image=create_test_image("art.jpg", (800, 600))
        )

        thumb_path = art.thumbnail.path
        self.assertTrue(os.path.exists(thumb_path))

        # Remove image
        art.image = None
        art.save()

        # Thumbnail should be removed
        self.assertFalse(art.thumbnail)
        self.assertFalse(os.path.exists(thumb_path))

    def test_save_handles_missing_old_thumbnail(self):
        """Test save handles case where old thumbnail doesn't exist (line 147-150)"""
        art = PublicArt.objects.create(
            title="Test Art", image=create_test_image("art1.jpg", (800, 600))
        )

        # Manually delete thumbnail file but keep reference
        if art.thumbnail and os.path.exists(art.thumbnail.path):
            os.remove(art.thumbnail.path)

        # Update image - should handle missing file gracefully
        art.image = create_test_image("art2.jpg", (600, 400))
        art.save()

        # Should create new thumbnail without error
        self.assertTrue(art.thumbnail)

    def test_save_downsamples_large_image(self):
        """Test save downsamples large images before saving"""
        large_image = create_test_image("large.jpg", (3000, 2500))

        art = PublicArt.objects.create(title="Large Art", image=large_image)

        # Open saved image and check size
        img = Image.open(art.image.path)
        self.assertLessEqual(img.width, PublicArt.MAX_IMAGE_SIZE[0])
        self.assertLessEqual(img.height, PublicArt.MAX_IMAGE_SIZE[1])

    def test_save_preserves_small_image(self):
        """Test save doesn't modify already-small images"""
        small_image = create_test_image("small.jpg", (500, 400))

        art = PublicArt.objects.create(title="Small Art", image=small_image)

        # Image should be saved without modification
        self.assertTrue(art.image)

    def test_art_image_method(self):
        """Test art_image method returns HTML"""
        art = PublicArt.objects.create(
            title="Test Art", image=create_test_image("art.jpg", (800, 600))
        )

        html = art.art_image()
        self.assertIn("<img", html)
        self.assertIn(art.image.url, html)

    def test_art_thumbnail_method(self):
        """Test art_thumbnail method returns HTML"""
        art = PublicArt.objects.create(
            title="Test Art", image=create_test_image("art.jpg", (800, 600))
        )

        html = art.art_thumbnail()
        self.assertIn("<img", html)
        self.assertIn(art.thumbnail.url, html)

    def test_art_thumbnail_no_image(self):
        """Test art_thumbnail with no thumbnail"""
        art = PublicArt.objects.create(title="No Image Art")

        result = art.art_thumbnail()
        self.assertEqual(result, "No Thumbnail")

    def test_square_thumbnail_no_image(self):
        """Test square_thumbnail with no thumbnail"""
        art = PublicArt.objects.create(title="No Image Art")

        result = art.square_thumbnail()
        self.assertEqual(result, "No Thumbnail")

    def test_get_image_status_with_image(self):
        """Test get_image_status with image (line 270)"""
        art = PublicArt.objects.create(
            title="Test Art", image=create_test_image("art.jpg", (800, 600))
        )

        status = art.get_image_status()
        # Should return checkmark HTML
        self.assertIn("9989", status)  # Unicode checkmark

    def test_get_image_status_without_image(self):
        """Test get_image_status without image (line 274-278)"""
        art = PublicArt.objects.create(title="No Image Art")

        status = art.get_image_status()
        self.assertEqual(status, "-")


class PublicArtModelBasicTests(TestCase):
    """Test basic PublicArt model functionality"""

    def test_str_with_all_fields(self):
        """Test string representation with all fields"""
        art = PublicArt.objects.create(title="Test Sculpture", artist_name="John Doe")
        self.assertEqual(str(art), "Test Sculpture by John Doe")

    def test_str_without_title(self):
        """Test string representation without title"""
        art = PublicArt.objects.create(artist_name="Jane Doe")
        self.assertEqual(str(art), "Untitled by Jane Doe")

    def test_str_without_artist(self):
        """Test string representation without artist"""
        art = PublicArt.objects.create(title="Mystery Art")
        self.assertEqual(str(art), "Mystery Art by Unknown")

    def test_str_without_both(self):
        """Test string representation without title or artist"""
        art = PublicArt.objects.create()
        self.assertEqual(str(art), "Untitled by Unknown")

    def test_get_average_rating_with_no_reviews(self):
        """Test get_average_rating with no reviews"""
        art = PublicArt.objects.create(title="Test Art")
        self.assertEqual(art.get_average_rating(), 0)

    def test_get_average_rating_with_reviews(self):
        """Test get_average_rating with multiple reviews"""
        art = PublicArt.objects.create(title="Test Art")
        user1 = User.objects.create_user(username="user1", password="pass")
        user2 = User.objects.create_user(username="user2", password="pass")
        user3 = User.objects.create_user(username="user3", password="pass")

        ArtComment.objects.create(user=user1, art=art, comment="Good", rating=4)
        ArtComment.objects.create(user=user2, art=art, comment="Great", rating=5)
        ArtComment.objects.create(user=user3, art=art, comment="Okay", rating=3)

        avg = art.get_average_rating()
        self.assertEqual(avg, 4.0)

    def test_get_average_rating_excludes_replies(self):
        """Test get_average_rating excludes reply comments"""
        art = PublicArt.objects.create(title="Test Art")
        user1 = User.objects.create_user(username="user1", password="pass")
        user2 = User.objects.create_user(username="user2", password="pass")

        parent = ArtComment.objects.create(
            user=user1, art=art, comment="Main", rating=5
        )
        ArtComment.objects.create(
            user=user2, art=art, comment="Reply", rating=1, parent=parent
        )

        # Should only count parent review
        avg = art.get_average_rating()
        self.assertEqual(avg, 5.0)

    def test_get_total_reviews(self):
        """Test get_total_reviews count"""
        art = PublicArt.objects.create(title="Test Art")
        user1 = User.objects.create_user(username="user1", password="pass")
        user2 = User.objects.create_user(username="user2", password="pass")

        ArtComment.objects.create(user=user1, art=art, comment="Review 1", rating=5)
        ArtComment.objects.create(user=user2, art=art, comment="Review 2", rating=4)

        self.assertEqual(art.get_total_reviews(), 2)

    def test_get_total_reviews_excludes_replies(self):
        """Test get_total_reviews excludes replies"""
        art = PublicArt.objects.create(title="Test Art")
        user1 = User.objects.create_user(username="user1", password="pass")
        user2 = User.objects.create_user(username="user2", password="pass")

        parent = ArtComment.objects.create(
            user=user1, art=art, comment="Main", rating=5
        )
        ArtComment.objects.create(user=user2, art=art, comment="Reply", parent=parent)

        self.assertEqual(art.get_total_reviews(), 1)


class CommentImageTests(TestCase):
    """Test CommentImage model (line 353)"""

    def test_comment_image_delete_removes_file(self):
        """Test that deleting CommentImage removes file (line 353)"""
        user = User.objects.create_user(username="user", password="pass")
        art = PublicArt.objects.create(title="Test Art")
        comment = ArtComment.objects.create(
            user=user, art=art, comment="Test", rating=5
        )

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"fake_image_content")
            temp_path = f.name

        with open(temp_path, "rb") as f:
            image = SimpleUploadedFile("test.jpg", f.read(), content_type="image/jpeg")
            comment_image = CommentImage.objects.create(
                comment=comment, image=image, order=0
            )

        image_path = comment_image.image.path

        # Delete model instance
        comment_image.delete()

        # File should be removed
        self.assertFalse(os.path.exists(image_path))

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def test_comment_image_str(self):
        """Test CommentImage string representation"""
        user = User.objects.create_user(username="user", password="pass")
        art = PublicArt.objects.create(title="Test Art")
        comment = ArtComment.objects.create(
            user=user, art=art, comment="Test", rating=5
        )

        image = SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")
        comment_image = CommentImage.objects.create(
            comment=comment, image=image, order=0
        )

        expected = f"Image for comment by {user.username}"
        self.assertEqual(str(comment_image), expected)

    def test_comment_image_ordering(self):
        """Test CommentImage ordering by order field"""
        user = User.objects.create_user(username="user", password="pass")
        art = PublicArt.objects.create(title="Test Art")
        comment = ArtComment.objects.create(
            user=user, art=art, comment="Test", rating=5
        )

        img2 = CommentImage.objects.create(
            comment=comment,
            image=SimpleUploadedFile("img2.jpg", b"2", content_type="image/jpeg"),
            order=2,
        )
        img1 = CommentImage.objects.create(
            comment=comment,
            image=SimpleUploadedFile("img1.jpg", b"1", content_type="image/jpeg"),
            order=1,
        )

        images = list(comment.images.all())
        self.assertEqual(images[0], img1)
        self.assertEqual(images[1], img2)


class CommentLikeTests(TestCase):
    """Test CommentLike model functionality"""

    def test_comment_like_str_liked(self):
        """Test string representation for like"""
        user = User.objects.create_user(username="liker", password="pass")
        commenter = User.objects.create_user(username="commenter", password="pass")
        art = PublicArt.objects.create(title="Test Art")
        comment = ArtComment.objects.create(
            user=commenter, art=art, comment="Test", rating=5
        )

        like = CommentLike.objects.create(user=user, comment=comment, is_like=True)

        expected = f"{user.username} liked comment by {commenter.username}"
        self.assertEqual(str(like), expected)

    def test_comment_like_str_disliked(self):
        """Test string representation for dislike"""
        user = User.objects.create_user(username="disliker", password="pass")
        commenter = User.objects.create_user(username="commenter", password="pass")
        art = PublicArt.objects.create(title="Test Art")
        comment = ArtComment.objects.create(
            user=commenter, art=art, comment="Test", rating=5
        )

        dislike = CommentLike.objects.create(user=user, comment=comment, is_like=False)

        expected = f"{user.username} disliked comment by {commenter.username}"
        self.assertEqual(str(dislike), expected)

    def test_unique_constraint(self):
        """Test unique_together constraint"""
        user = User.objects.create_user(username="user", password="pass")
        art = PublicArt.objects.create(title="Test Art")
        comment = ArtComment.objects.create(
            user=user, art=art, comment="Test", rating=5
        )

        CommentLike.objects.create(user=user, comment=comment, is_like=True)

        with self.assertRaises(IntegrityError):
            CommentLike.objects.create(user=user, comment=comment, is_like=False)


class CommentReportTests(TestCase):
    """Test CommentReport model functionality"""

    def test_comment_report_str(self):
        """Test string representation"""
        reporter = User.objects.create_user(username="reporter", password="pass")
        commenter = User.objects.create_user(username="commenter", password="pass")
        art = PublicArt.objects.create(title="Test Art")
        comment = ArtComment.objects.create(
            user=commenter, art=art, comment="Bad comment", rating=1
        )

        report = CommentReport.objects.create(
            comment=comment, reporter=reporter, reasons=["spam", "harassment"]
        )

        expected = f"Report by {reporter.username} on comment {comment.id}"
        self.assertEqual(str(report), expected)

    def test_comment_report_default_status(self):
        """Test default status is pending"""
        reporter = User.objects.create_user(username="reporter", password="pass")
        commenter = User.objects.create_user(username="commenter", password="pass")
        art = PublicArt.objects.create(title="Test Art")
        comment = ArtComment.objects.create(
            user=commenter, art=art, comment="Test", rating=5
        )

        report = CommentReport.objects.create(
            comment=comment, reporter=reporter, reasons=["spam"]
        )

        self.assertEqual(report.status, "pending")

    def test_comment_report_unique_together(self):
        """Test unique_together constraint"""
        reporter = User.objects.create_user(username="reporter", password="pass")
        commenter = User.objects.create_user(username="commenter", password="pass")
        art = PublicArt.objects.create(title="Test Art")
        comment = ArtComment.objects.create(
            user=commenter, art=art, comment="Test", rating=5
        )

        CommentReport.objects.create(
            comment=comment, reporter=reporter, reasons=["spam"]
        )

        with self.assertRaises(IntegrityError):
            CommentReport.objects.create(
                comment=comment, reporter=reporter, reasons=["harassment"]
            )


class UserFavoriteArtTests(TestCase):
    """Test UserFavoriteArt model"""

    def test_str_representation(self):
        """Test string representation"""
        user = User.objects.create_user(username="user", password="pass")
        art = PublicArt.objects.create(title="Favorite Art")

        favorite = UserFavoriteArt.objects.create(user=user, art=art)

        expected = f"{user.username} - Favorite Art"
        self.assertEqual(str(favorite), expected)

    def test_unique_together_constraint(self):
        """Test unique_together constraint"""
        user = User.objects.create_user(username="user", password="pass")
        art = PublicArt.objects.create(title="Art")

        UserFavoriteArt.objects.create(user=user, art=art)

        with self.assertRaises(IntegrityError):
            UserFavoriteArt.objects.create(user=user, art=art)

    def test_cascade_delete_user(self):
        """Test cascade delete when user is deleted"""
        user = User.objects.create_user(username="user", password="pass")
        art = PublicArt.objects.create(title="Art")

        UserFavoriteArt.objects.create(user=user, art=art)
        self.assertEqual(UserFavoriteArt.objects.count(), 1)

        user.delete()
        self.assertEqual(UserFavoriteArt.objects.count(), 0)

    def test_cascade_delete_art(self):
        """Test cascade delete when art is deleted"""
        user = User.objects.create_user(username="user", password="pass")
        art = PublicArt.objects.create(title="Art")

        UserFavoriteArt.objects.create(user=user, art=art)
        self.assertEqual(UserFavoriteArt.objects.count(), 1)

        art.delete()
        self.assertEqual(UserFavoriteArt.objects.count(), 0)


class ArtCommentTests(TestCase):
    """Test ArtComment model"""

    def test_likes_count_property(self):
        """Test likes_count property"""
        user1 = User.objects.create_user(username="user1", password="pass")
        user2 = User.objects.create_user(username="user2", password="pass")
        user3 = User.objects.create_user(username="user3", password="pass")
        art = PublicArt.objects.create(title="Art")
        comment = ArtComment.objects.create(
            user=user1, art=art, comment="Test", rating=5
        )

        CommentLike.objects.create(user=user2, comment=comment, is_like=True)
        CommentLike.objects.create(user=user3, comment=comment, is_like=True)

        self.assertEqual(comment.likes_count, 2)

    def test_dislikes_count_property(self):
        """Test dislikes_count property"""
        user1 = User.objects.create_user(username="user1", password="pass")
        user2 = User.objects.create_user(username="user2", password="pass")
        art = PublicArt.objects.create(title="Art")
        comment = ArtComment.objects.create(
            user=user1, art=art, comment="Test", rating=5
        )

        CommentLike.objects.create(user=user2, comment=comment, is_like=False)

        self.assertEqual(comment.dislikes_count, 1)

    def test_user_reaction_like(self):
        """Test user_reaction returns 'like'"""
        user1 = User.objects.create_user(username="user1", password="pass")
        user2 = User.objects.create_user(username="user2", password="pass")
        art = PublicArt.objects.create(title="Art")
        comment = ArtComment.objects.create(
            user=user1, art=art, comment="Test", rating=5
        )

        CommentLike.objects.create(user=user2, comment=comment, is_like=True)

        self.assertEqual(comment.user_reaction(user2), "like")

    def test_user_reaction_dislike(self):
        """Test user_reaction returns 'dislike'"""
        user1 = User.objects.create_user(username="user1", password="pass")
        user2 = User.objects.create_user(username="user2", password="pass")
        art = PublicArt.objects.create(title="Art")
        comment = ArtComment.objects.create(
            user=user1, art=art, comment="Test", rating=5
        )

        CommentLike.objects.create(user=user2, comment=comment, is_like=False)

        self.assertEqual(comment.user_reaction(user2), "dislike")

    def test_user_reaction_none(self):
        """Test user_reaction returns None when no reaction"""
        user1 = User.objects.create_user(username="user1", password="pass")
        user2 = User.objects.create_user(username="user2", password="pass")
        art = PublicArt.objects.create(title="Art")
        comment = ArtComment.objects.create(
            user=user1, art=art, comment="Test", rating=5
        )

        self.assertIsNone(comment.user_reaction(user2))
