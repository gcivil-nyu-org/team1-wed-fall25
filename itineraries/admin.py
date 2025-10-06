from django.contrib import admin
from .models import Itinerary, ItineraryItem


class ItineraryItemInline(admin.TabularInline):
    model = ItineraryItem
    extra = 1
    fields = ('location', 'order_index', 'note', 'planned_start', 'planned_end')
    raw_id_fields = ('location',)


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'is_public', 'item_count', 'created_at', 'updated_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('title', 'owner__username', 'notes')
    readonly_fields = ('share_token', 'created_at', 'updated_at')
    inlines = [ItineraryItemInline]
    raw_id_fields = ('owner',)
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'


@admin.register(ItineraryItem)
class ItineraryItemAdmin(admin.ModelAdmin):
    list_display = ('itinerary', 'order_index', 'location', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('itinerary__title', 'location__name')
    raw_id_fields = ('itinerary', 'location')
