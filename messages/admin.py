from django.contrib import admin
from .models import Conversation, PrivateMessage, UserOnlineStatus


@admin.register(UserOnlineStatus)
class UserOnlineStatusAdmin(admin.ModelAdmin):
    list_display = ["user", "is_online", "last_seen"]
    list_filter = ["is_online"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["last_seen"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "user1", "user2", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["user1__username", "user2__username"]
    raw_id_fields = ["user1", "user2"]


@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "sender", "short_content", "is_read", "created_at"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["sender__username", "content"]
    raw_id_fields = ["conversation", "sender"]
    readonly_fields = ["created_at"]

    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    short_content.short_description = "Content"

