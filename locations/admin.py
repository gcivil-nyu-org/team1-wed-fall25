from django.contrib import admin
from .models import Tag, Location, Favorite


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category')
    search_fields = ('name', 'category')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'source', 'average_rating', 'review_count', 'is_active', 'created_at')
    list_filter = ('source', 'is_active', 'city', 'created_at')
    search_fields = ('name', 'description', 'address')
    filter_horizontal = ('tags',)
    readonly_fields = ('average_rating', 'review_count', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'tags')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Geolocation', {
            'fields': ('latitude', 'longitude')
        }),
        ('Media', {
            'fields': ('website_url', 'image_url')
        }),
        ('Source & Status', {
            'fields': ('source', 'source_id', 'created_by', 'is_active')
        }),
        ('Stats', {
            'fields': ('average_rating', 'review_count', 'created_at', 'updated_at')
        }),
    )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'location__name')
    raw_id_fields = ('user', 'location')
