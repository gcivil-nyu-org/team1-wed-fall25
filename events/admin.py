from django.contrib import admin
from .models import Event, EventLocation, Invitation, RSVP


class EventLocationInline(admin.TabularInline):
    model = EventLocation
    extra = 1
    raw_id_fields = ('location',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'visibility', 'start_time', 'attendee_count', 'is_active')
    list_filter = ('visibility', 'is_active', 'start_time')
    search_fields = ('title', 'description', 'owner__username')
    readonly_fields = ('share_token', 'created_at', 'updated_at')
    inlines = [EventLocationInline]
    raw_id_fields = ('owner', 'itinerary')


@admin.register(EventLocation)
class EventLocationAdmin(admin.ModelAdmin):
    list_display = ('event', 'location', 'order_index')
    list_filter = ('event',)
    raw_id_fields = ('event', 'location')


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('event', 'inviter', 'invited_user', 'invited_email', 'status', 'created_at')
    list_filter = ('status', 'role', 'created_at')
    search_fields = ('event__title', 'invited_user__username', 'invited_email')
    readonly_fields = ('token', 'created_at')
    raw_id_fields = ('event', 'inviter', 'invited_user')


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'event__title')
    raw_id_fields = ('event', 'user')
