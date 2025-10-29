from django.contrib import admin
from .models import UserProfile, UserFollow


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "full_name", "privacy", "created_at"]
    list_filter = ["privacy", "created_at"]
    search_fields = ["user__username", "user__email", "full_name"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        ("User", {"fields": ("user",)}),
        (
            "Profile Information",
            {"fields": ("full_name", "about", "contact_info", "profile_image")},
        ),
        ("Settings", {"fields": ("privacy",)}),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ["follower", "following", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["follower__username", "following__username"]
    readonly_fields = ["created_at"]

    def has_add_permission(self, request):
        # Prevent manual creation through admin
        return False
