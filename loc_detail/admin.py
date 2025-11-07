from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import PublicArt, UserFavoriteArt, ArtComment, CommentImage, CommentReport


@admin.register(PublicArt)
class PublicArtAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "artist_name",
        "get_image_status",
        "borough",
        "year_created",
        "agency",
    ]
    list_filter = ["borough", "agency", "year_created"]
    search_fields = ["title", "artist_name", "description", "location"]
    readonly_fields = ["created_at", "updated_at", "external_id", "art_thumbnail"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "title",
                    "artist_name",
                    "description",
                    "image",
                    "art_thumbnail",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "location",
                    "borough",
                    "latitude",
                    "longitude",
                    "community_board",
                )
            },
        ),
        (
            "Art Details",
            {"fields": ("medium", "dimensions", "year_created", "year_dedicated")},
        ),
        ("Administrative", {"fields": ("agency", "external_id")}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(UserFavoriteArt)
class UserFavoriteArtAdmin(admin.ModelAdmin):
    list_display = ["user", "art", "added_at"]
    list_filter = ["added_at"]
    search_fields = ["user__username", "art__title", "notes"]
    readonly_fields = ["added_at"]


class CommentImageInline(admin.TabularInline):
    model = CommentImage
    extra = 0
    fields = ["image", "order", "uploaded_at"]
    readonly_fields = ["uploaded_at"]


@admin.register(ArtComment)
class ArtCommentAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "art",
        "rating",
        "created_at",
        "comment_preview",
        "has_images",
        "report_count",
    ]
    list_filter = ["created_at", "rating"]
    search_fields = ["user__username", "art__title", "comment"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [CommentImageInline]

    def comment_preview(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment

    comment_preview.short_description = "Comment Preview"

    def has_images(self, obj):
        count = obj.images.count()
        if count > 0:
            return format_html(
                '<span style="color: green;">✓ {} image(s)</span>', count
            )
        return format_html('<span style="color: gray;">No images</span>')

    has_images.short_description = "Images"

    def report_count(self, obj):
        count = obj.reports.count()
        if count > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ {} report(s)</span>',
                count,
            )
        return format_html('<span style="color: green;">No reports</span>')

    report_count.short_description = "Reports"


@admin.register(CommentImage)
class CommentImageAdmin(admin.ModelAdmin):
    list_display = [
        "comment_user",
        "comment_art",
        "uploaded_at",
        "order",
        "image_preview",
    ]
    list_filter = ["uploaded_at"]
    search_fields = ["comment__user__username", "comment__art__title"]
    readonly_fields = ["uploaded_at", "image_preview"]

    def comment_user(self, obj):
        return obj.comment.user.username

    comment_user.short_description = "User"

    def comment_art(self, obj):
        return obj.comment.art.title

    comment_art.short_description = "Art Location"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.image.url,
            )
        return "No image"

    image_preview.short_description = "Preview"


@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "comment_preview",
        "reporter",
        "status",
        "reasons_display",
        "created_at",
        "reviewed_status",
    ]
    list_filter = ["status", "created_at", "reasons"]
    search_fields = [
        "reporter__username",
        "comment__user__username",
        "comment__comment",
        "additional_info",
    ]
    readonly_fields = ["created_at", "comment_detail", "reporter_detail"]

    fieldsets = (
        (
            "Report Information",
            {
                "fields": (
                    "comment_detail",
                    "reporter_detail",
                    "reasons",
                    "additional_info",
                )
            },
        ),
        ("Status", {"fields": ("status", "reviewed_at", "reviewed_by", "admin_notes")}),
    )

    actions = ["mark_as_reviewing", "mark_as_resolved", "mark_as_dismissed"]

    def comment_preview(self, obj):
        text = obj.comment.comment[:50]
        return text + "..." if len(obj.comment.comment) > 50 else text

    comment_preview.short_description = "Comment"

    def reasons_display(self, obj):
        if isinstance(obj.reasons, list):
            reasons_text = ", ".join(obj.reasons)
            return format_html('<span style="color: #c00;">{}</span>', reasons_text)
        return str(obj.reasons)

    reasons_display.short_description = "Reasons"

    def reviewed_status(self, obj):
        if obj.status == "pending":
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏳ Pending</span>'
            )
        elif obj.status == "reviewing":
            return format_html(
                '<span style="color: blue; font-weight: bold;">🔍 Reviewing</span>'
            )
        elif obj.status == "resolved":
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Resolved</span>'
            )
        else:
            return format_html('<span style="color: gray;">✗ Dismissed</span>')

    reviewed_status.short_description = "Status"

    def comment_detail(self, obj):
        return format_html(
            '<div style="margin-bottom: 10px;"><strong>Comment ID:</strong> {}<br>'
            "<strong>Author:</strong> {}<br>"
            "<strong>Art Location:</strong> {}<br>"
            '<strong>Full Comment:</strong><br><div style="background: #f5f5f5; '
            'padding: 10px; margin-top: 5px; border-radius: 4px;">{}</div></div>',
            obj.comment.id,
            obj.comment.user.username,
            obj.comment.art.title,
            obj.comment.comment,
        )

    comment_detail.short_description = "Comment Details"

    def reporter_detail(self, obj):
        return format_html(
            "<strong>Username:</strong> {}<br>"
            "<strong>Email:</strong> {}<br>"
            "<strong>Joined:</strong> {}",
            obj.reporter.username,
            obj.reporter.email,
            obj.reporter.date_joined.strftime("%Y-%m-%d"),
        )

    reporter_detail.short_description = "Reporter Details"

    def mark_as_reviewing(self, request, queryset):
        queryset.update(status="reviewing")
        self.message_user(
            request, f"{queryset.count()} report(s) marked as under review."
        )

    mark_as_reviewing.short_description = "Mark as Under Review"

    def mark_as_resolved(self, request, queryset):
        queryset.update(
            status="resolved", reviewed_at=timezone.now(), reviewed_by=request.user
        )
        self.message_user(request, f"{queryset.count()} report(s) marked as resolved.")

    mark_as_resolved.short_description = "Mark as Resolved"

    def mark_as_dismissed(self, request, queryset):
        queryset.update(
            status="dismissed", reviewed_at=timezone.now(), reviewed_by=request.user
        )
        self.message_user(request, f"{queryset.count()} report(s) dismissed.")

    mark_as_dismissed.short_description = "Dismiss Reports"
