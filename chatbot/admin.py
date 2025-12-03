from django.contrib import admin
from .models import ChatSession, ChatMessage


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ["user", "session_id", "created_at", "updated_at", "message_count"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["user__username", "session_id"]
    readonly_fields = ["session_id", "created_at", "updated_at"]

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = "Messages"


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "session_user",
        "sender",
        "message_preview",
        "created_at",
        "has_metadata",
    ]
    list_filter = ["sender", "created_at"]
    search_fields = ["message", "session__user__username"]
    readonly_fields = ["created_at", "formatted_metadata"]

    fieldsets = (
        ("Message Info", {"fields": ("session", "sender", "message", "created_at")}),
        ("Metadata", {"fields": ("formatted_metadata",), "classes": ("collapse",)}),
    )

    def session_user(self, obj):
        return obj.session.user.username

    session_user.short_description = "User"

    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message

    message_preview.short_description = "Message"

    def has_metadata(self, obj):
        return bool(obj.metadata)

    has_metadata.boolean = True
    has_metadata.short_description = "Has Metadata"

    def formatted_metadata(self, obj):
        if obj.metadata:
            import json

            return json.dumps(obj.metadata, indent=2)
        return "No metadata"

    formatted_metadata.short_description = "Metadata (JSON)"
