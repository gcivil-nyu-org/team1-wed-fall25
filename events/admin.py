from django.contrib import admin
from .models import (
    Event,
    EventLocation,
    EventMembership,
    EventChatMessage,
    EventJoinRequest,
    MessageReport,
)


class EventLocationInline(admin.TabularInline):
    model = EventLocation
    extra = 1
    max_num = 5


class EventMembershipInline(admin.TabularInline):
    model = EventMembership
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "host", "start_time", "visibility", "created_at"]
    list_filter = ["visibility", "start_time", "created_at"]
    search_fields = ["title", "host__username"]
    readonly_fields = ["slug", "created_at", "updated_at"]
    inlines = [EventLocationInline, EventMembershipInline]


@admin.register(EventChatMessage)
class EventChatMessageAdmin(admin.ModelAdmin):
    list_display = ["event", "author", "message", "created_at"]
    list_filter = ["event", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(EventJoinRequest)
class EventJoinRequestAdmin(admin.ModelAdmin):
    list_display = ["event", "requester", "status", "created_at"]
    list_filter = ["status", "event"]


@admin.register(MessageReport)
class MessageReportAdmin(admin.ModelAdmin):
    list_display = ["message", "reporter", "reason", "status", "created_at"]
    list_filter = ["status", "reason", "created_at"]
    search_fields = ["message__message", "reporter__username", "description"]
    readonly_fields = ["created_at", "reviewed_at"]
    list_editable = ["status"]
