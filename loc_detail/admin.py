from django.contrib import admin
from .models import PublicArt, UserFavoriteArt, ArtComment


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


@admin.register(ArtComment)
class ArtCommentAdmin(admin.ModelAdmin):
    list_display = ["user", "art", "created_at", "comment_preview"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "art__title", "comment"]
    readonly_fields = ["created_at", "updated_at"]

    def comment_preview(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment

    comment_preview.short_description = "Comment Preview"
