"""
Admin configuration for itineraries app
"""

from django.contrib import admin
from .models import Itinerary, ItineraryStop


class ItineraryStopInline(admin.TabularInline):
    model = ItineraryStop
    extra = 1
    fields = ["order", "location", "visit_time", "notes"]
    ordering = ["order"]


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["title", "description", "user__username"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ItineraryStopInline]


@admin.register(ItineraryStop)
class ItineraryStopAdmin(admin.ModelAdmin):
    list_display = ["itinerary", "location", "order", "visit_time"]
    list_filter = ["itinerary", "visit_time"]
    search_fields = ["itinerary__title", "location__title"]
    ordering = ["itinerary", "order"]
