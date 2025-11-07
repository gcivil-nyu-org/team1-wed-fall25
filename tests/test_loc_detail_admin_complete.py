"""
Complete test coverage for loc_detail/admin.py
Targets all missing lines to achieve 95%+ coverage
"""

from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages.storage.fallback import FallbackStorage


from loc_detail.models import (
    PublicArt,
    UserFavoriteArt,
    ArtComment,
    CommentImage,
    CommentReport,
)
from loc_detail.admin import (
    PublicArtAdmin,
    UserFavoriteArtAdmin,
    ArtCommentAdmin,
    CommentImageAdmin,
    CommentReportAdmin,
)


class PublicArtAdminTests(TestCase):
    """Test PublicArtAdmin functionality"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = PublicArtAdmin(PublicArt, self.site)
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin123"
        )

    def test_list_display_fields(self):
        """Test list_display includes correct fields"""
        expected_fields = [
            "title",
            "artist_name",
            "get_image_status",
            "borough",
            "year_created",
            "agency",
        ]
        self.assertEqual(self.admin.list_display, expected_fields)

    def test_list_filter_fields(self):
        """Test list_filter includes correct fields"""
        expected_filters = ["borough", "agency", "year_created"]
        self.assertEqual(self.admin.list_filter, expected_filters)

    def test_search_fields(self):
        """Test search_fields includes correct fields"""
        expected_fields = ["title", "artist_name", "description", "location"]
        self.assertEqual(self.admin.search_fields, expected_fields)

    def test_readonly_fields(self):
        """Test readonly_fields"""
        expected = ["created_at", "updated_at", "external_id", "art_thumbnail"]
        self.assertEqual(self.admin.readonly_fields, expected)

    def test_fieldsets_structure(self):
        """Test fieldsets are properly structured"""
        self.assertEqual(len(self.admin.fieldsets), 5)


class UserFavoriteArtAdminTests(TestCase):
    """Test UserFavoriteArtAdmin functionality"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = UserFavoriteArtAdmin(UserFavoriteArt, self.site)
        self.user = User.objects.create_user(username="user", password="pass")
        self.art = PublicArt.objects.create(title="Test Art")

    def test_list_display_fields(self):
        """Test list_display includes correct fields"""
        expected = ["user", "art", "added_at"]
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter_fields(self):
        """Test list_filter"""
        self.assertEqual(self.admin.list_filter, ["added_at"])

    def test_search_fields(self):
        """Test search_fields"""
        expected = ["user__username", "art__title", "notes"]
        self.assertEqual(self.admin.search_fields, expected)


class ArtCommentAdminTests(TestCase):
    """Test ArtCommentAdmin functionality (lines 90-111)"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ArtCommentAdmin(ArtComment, self.site)
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="user", password="pass")
        self.art = PublicArt.objects.create(title="Test Art")

    def test_comment_preview_short_text(self):
        """Test comment_preview with short comment (line 90)"""
        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Short comment", rating=5
        )

        preview = self.admin.comment_preview(comment)
        self.assertEqual(preview, "Short comment")

    def test_comment_preview_long_text(self):
        """Test comment_preview with long comment (line 90)"""
        long_text = "a" * 60
        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment=long_text, rating=5
        )

        preview = self.admin.comment_preview(comment)
        self.assertEqual(len(preview), 53)  # 50 chars + "..."
        self.assertTrue(preview.endswith("..."))

    def test_has_images_with_images(self):
        """Test has_images method when comment has images (lines 95-100)"""
        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Test", rating=5
        )

        # Add images
        for i in range(2):
            image = SimpleUploadedFile(
                f"test{i}.jpg", b"fake_image", content_type="image/jpeg"
            )
            CommentImage.objects.create(comment=comment, image=image, order=i)

        result = self.admin.has_images(comment)

        # Should contain checkmark and count
        self.assertIn("✓", result)
        self.assertIn("2", result)
        self.assertIn("image(s)", result)
        self.assertIn("green", result.lower())

    def test_has_images_without_images(self):
        """Test has_images method when comment has no images (line 101)"""
        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Test", rating=5
        )

        result = self.admin.has_images(comment)

        self.assertIn("No images", result)
        self.assertIn("gray", result.lower())

    def test_report_count_with_reports(self):
        """Test report_count method with reports (lines 105-111)"""
        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Reported comment", rating=1
        )

        # Create reports
        reporter1 = User.objects.create_user(username="reporter1", password="pass")
        reporter2 = User.objects.create_user(username="reporter2", password="pass")

        CommentReport.objects.create(
            comment=comment, reporter=reporter1, reasons=["spam"]
        )
        CommentReport.objects.create(
            comment=comment, reporter=reporter2, reasons=["harassment"]
        )

        result = self.admin.report_count(comment)

        self.assertIn("⚠", result)
        self.assertIn("2", result)
        self.assertIn("report(s)", result)
        self.assertIn("red", result.lower())
        self.assertIn("bold", result.lower())

    def test_report_count_without_reports(self):
        """Test report_count method without reports"""
        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Clean comment", rating=5
        )

        result = self.admin.report_count(comment)

        self.assertIn("No reports", result)
        self.assertIn("green", result.lower())


class CommentImageAdminTests(TestCase):
    """Test CommentImageAdmin functionality (lines 130-145)"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = CommentImageAdmin(CommentImage, self.site)
        self.user = User.objects.create_user(username="user", password="pass")
        self.art = PublicArt.objects.create(title="Test Art")
        self.comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Test", rating=5
        )

    def test_comment_user_method(self):
        """Test comment_user method (line 130)"""
        image = SimpleUploadedFile("test.jpg", b"fake", content_type="image/jpeg")
        comment_image = CommentImage.objects.create(
            comment=self.comment, image=image, order=0
        )

        result = self.admin.comment_user(comment_image)
        self.assertEqual(result, self.user.username)

    def test_comment_art_method(self):
        """Test comment_art method (line 135)"""
        image = SimpleUploadedFile("test.jpg", b"fake", content_type="image/jpeg")
        comment_image = CommentImage.objects.create(
            comment=self.comment, image=image, order=0
        )

        result = self.admin.comment_art(comment_image)
        self.assertEqual(result, self.art.title)

    def test_image_preview_with_image(self):
        """Test image_preview method with valid image (lines 140-145)"""
        image = SimpleUploadedFile("test.jpg", b"fake", content_type="image/jpeg")
        comment_image = CommentImage.objects.create(
            comment=self.comment, image=image, order=0
        )

        result = self.admin.image_preview(comment_image)

        self.assertIn("<img", result)
        self.assertIn(comment_image.image.url, result)
        self.assertIn("200px", result)

    def test_image_preview_without_image(self):
        """Test image_preview without image"""
        # Create without image (edge case)
        comment_image = CommentImage(comment=self.comment, order=0)

        result = self.admin.image_preview(comment_image)
        self.assertEqual(result, "No image")


class CommentReportAdminTests(TestCase):
    """Test CommentReportAdmin functionality (lines 188-266)"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = CommentReportAdmin(CommentReport, self.site)
        self.factory = RequestFactory()
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin123"
        )
        self.reporter = User.objects.create_user(
            username="reporter", email="reporter@test.com", password="pass"
        )
        self.commenter = User.objects.create_user(username="commenter", password="pass")
        self.art = PublicArt.objects.create(title="Test Art")
        self.comment = ArtComment.objects.create(
            user=self.commenter, art=self.art, comment="Problematic comment", rating=1
        )
        self.report = CommentReport.objects.create(
            comment=self.comment,
            reporter=self.reporter,
            reasons=["spam", "harassment"],
            additional_info="This is inappropriate",
        )

    def _get_request_with_messages(self):
        """
        Build a RequestFactory request with a valid messages storage attached,
        so admin.message_user() works in tests.
        """
        request = self.factory.post("/admin/loc_detail/commentreport/")
        request.user = self.superuser
        # messages framework expects a session and a _messages storage
        setattr(request, "session", {})
        storage = FallbackStorage(request)
        setattr(request, "_messages", storage)
        return request

    def test_comment_preview_short(self):
        """Test comment_preview with short text (line 188-189)"""
        short_comment = ArtComment.objects.create(
            user=self.commenter, art=self.art, comment="Short", rating=3
        )
        report = CommentReport.objects.create(
            comment=short_comment, reporter=self.reporter, reasons=["spam"]
        )

        result = self.admin.comment_preview(report)
        self.assertEqual(result, "Short")

    def test_comment_preview_long(self):
        """Test comment_preview with long text (line 188-189)"""
        result = self.admin.comment_preview(self.report)

        self.assertLessEqual(len(result), 53)
        if len(self.report.comment.comment) > 50:
            self.assertTrue(result.endswith("."))

    def test_reasons_display_with_list(self):
        """Test reasons_display with list of reasons (lines 194-197)"""
        result = self.admin.reasons_display(self.report)

        self.assertIn("spam", result)
        self.assertIn("harassment", result)
        self.assertIn("#c00", result.lower())  # Red color

    def test_reasons_display_with_non_list(self):
        """Test reasons_display with non-list reasons"""
        # Manually set reasons to string (edge case)
        self.report.reasons = "spam"
        self.report.save()

        result = self.admin.reasons_display(self.report)
        self.assertIn("spam", result)

    def test_reviewed_status_pending(self):
        """Test reviewed_status for pending reports (lines 202-215)"""
        self.report.status = "pending"
        self.report.save()

        result = self.admin.reviewed_status(self.report)

        self.assertIn("⏳", result)
        self.assertIn("Pending", result)
        self.assertIn("orange", result.lower())
        self.assertIn("bold", result.lower())

    def test_reviewed_status_reviewing(self):
        """Test reviewed_status for reviewing reports"""
        self.report.status = "reviewing"
        self.report.save()

        result = self.admin.reviewed_status(self.report)

        self.assertIn("🔍", result)
        self.assertIn("Reviewing", result)
        self.assertIn("blue", result.lower())

    def test_reviewed_status_resolved(self):
        """Test reviewed_status for resolved reports"""
        self.report.status = "resolved"
        self.report.save()

        result = self.admin.reviewed_status(self.report)

        # admin.reviewed_status uses a plain checkmark, not an emoji
        self.assertIn("✓", result)
        self.assertIn("Resolved", result)
        self.assertIn("green", result.lower())
        self.assertIn("bold", result.lower())

    def test_reviewed_status_dismissed(self):
        """Test reviewed_status for dismissed reports"""
        self.report.status = "dismissed"
        self.report.save()

        result = self.admin.reviewed_status(self.report)

        # admin.reviewed_status uses a plain cross, not an emoji
        self.assertIn("✗", result)
        self.assertIn("Dismissed", result)
        self.assertIn("gray", result.lower())

    def test_mark_as_reviewing_action(self):
        """Test mark_as_reviewing action (lines 247-248)"""
        request = self._get_request_with_messages()
        queryset = CommentReport.objects.filter(id=self.report.id)

        self.admin.mark_as_reviewing(request, queryset)

        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "reviewing")

    def test_mark_as_resolved_action(self):
        """Test mark_as_resolved action (lines 255-258)"""
        request = self._get_request_with_messages()
        queryset = CommentReport.objects.filter(id=self.report.id)

        self.admin.mark_as_resolved(request, queryset)

        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "resolved")

    def test_mark_as_dismissed_action(self):
        """Test mark_as_dismissed action (lines 263-266)"""
        request = self._get_request_with_messages()
        queryset = CommentReport.objects.filter(id=self.report.id)

        self.admin.mark_as_dismissed(request, queryset)

        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "dismissed")

    def test_mark_as_reviewing_multiple_reports(self):
        """Test marking multiple reports as reviewing"""
        request = self._get_request_with_messages()

        # Create a second report
        report2 = CommentReport.objects.create(
            comment=self.comment,
            reporter=User.objects.create_user(username="reporter2", password="pass"),
            reasons=["spam"],
        )

        queryset = CommentReport.objects.filter(id__in=[self.report.id, report2.id])

        self.admin.mark_as_reviewing(request, queryset)

        self.assertEqual(CommentReport.objects.filter(status="reviewing").count(), 2)

    def test_actions_available(self):
        """Test that custom actions are registered"""
        request = self.factory.get("/admin/loc_detail/commentreport/")
        request.user = self.superuser

        actions = self.admin.get_actions(request)

        self.assertIn("mark_as_reviewing", actions)
        self.assertIn("mark_as_resolved", actions)
        self.assertIn("mark_as_dismissed", actions)


class AdminIntegrationTests(TestCase):
    """Integration tests for admin functionality"""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin123"
        )

    def test_public_art_admin_queryset(self):
        """Test PublicArtAdmin queryset filtering"""
        site = AdminSite()
        admin = PublicArtAdmin(PublicArt, site)

        # Create test data
        PublicArt.objects.create(title="Art 1", borough="Manhattan")
        PublicArt.objects.create(title="Art 2", borough="Brooklyn")

        request = RequestFactory().get("/admin/loc_detail/publicart/")
        request.user = self.superuser

        # Get changelist
        changelist = admin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)

        self.assertEqual(queryset.count(), 2)

    def test_comment_report_admin_queryset_ordering(self):
        """Test CommentReportAdmin queryset ordering"""
        site = AdminSite()
        admin = CommentReportAdmin(CommentReport, site)

        user = User.objects.create_user(username="user", password="pass")
        art = PublicArt.objects.create(title="Art")
        comment = ArtComment.objects.create(
            user=user, art=art, comment="Test", rating=5
        )

        # Create reports at different times
        report1 = CommentReport.objects.create(
            comment=comment, reporter=user, reasons=["spam"]
        )

        report2 = CommentReport.objects.create(
            comment=ArtComment.objects.create(
                user=user, art=art, comment="Test 2", rating=5
            ),
            reporter=user,
            reasons=["harassment"],
        )

        request = RequestFactory().get("/admin/loc_detail/commentreport/")
        request.user = self.superuser

        changelist = admin.get_changelist_instance(request)
        queryset = changelist.get_queryset(request)

        # Should be ordered by created_at descending
        reports = list(queryset)
        self.assertEqual(reports[0].id, report2.id)
        self.assertEqual(reports[1].id, report1.id)


class AdminDisplayMethodsEdgeCases(TestCase):
    """Test edge cases for admin display methods"""

    def setUp(self):
        self.site = AdminSite()
        self.user = User.objects.create_user(username="user", password="pass")
        self.art = PublicArt.objects.create(title="Test Art")

    def test_comment_preview_with_unicode(self):
        """Test comment_preview with unicode characters"""
        admin = ArtCommentAdmin(ArtComment, self.site)

        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Café ☕ émojis 😀 " * 10, rating=5
        )

        preview = admin.comment_preview(comment)
        self.assertIsInstance(preview, str)
        self.assertTrue(len(preview) <= 53)

    def test_has_images_with_zero_images(self):
        """Test has_images returns correct HTML for zero images"""
        admin = ArtCommentAdmin(ArtComment, self.site)

        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="No images", rating=5
        )

        result = admin.has_images(comment)
        self.assertIn("No images", result)

    def test_report_count_with_many_reports(self):
        """Test report_count with many reports"""
        admin = ArtCommentAdmin(ArtComment, self.site)

        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Heavily reported", rating=1
        )

        # Create 10 reports
        for i in range(10):
            reporter = User.objects.create_user(
                username=f"reporter{i}", password="pass"
            )
            CommentReport.objects.create(
                comment=comment, reporter=reporter, reasons=["spam"]
            )

        result = admin.report_count(comment)
        self.assertIn("10", result)
        self.assertIn("report(s)", result)

    def test_image_preview_with_missing_file(self):
        """Test image_preview when file is missing"""
        admin = CommentImageAdmin(CommentImage, self.site)

        comment = ArtComment.objects.create(
            user=self.user, art=self.art, comment="Test", rating=5
        )

        # Create comment image with image field but no actual file
        comment_image = CommentImage(comment=comment, order=0)

        result = admin.image_preview(comment_image)
        self.assertEqual(result, "No image")


class AdminFieldsetTests(TestCase):
    """Test admin fieldset configurations"""

    def test_public_art_admin_fieldsets(self):
        """Test PublicArtAdmin fieldsets structure"""
        site = AdminSite()
        admin = PublicArtAdmin(PublicArt, site)

        fieldsets = admin.fieldsets

        # Should have 5 sections
        self.assertEqual(len(fieldsets), 5)

        # Verify section names
        section_names = [fs[0] for fs in fieldsets]
        self.assertIn("Basic Information", section_names)
        self.assertIn("Location", section_names)
        self.assertIn("Art Details", section_names)
        self.assertIn("Administrative", section_names)
        self.assertIn("Metadata", section_names)

    def test_comment_report_admin_fieldsets(self):
        """Test CommentReportAdmin fieldsets structure"""
        site = AdminSite()
        admin = CommentReportAdmin(CommentReport, site)

        fieldsets = admin.fieldsets

        # Should have 2 sections
        self.assertEqual(len(fieldsets), 2)

        section_names = [fs[0] for fs in fieldsets]
        self.assertIn("Report Information", section_names)
        self.assertIn("Status", section_names)
