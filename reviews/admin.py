from django.contrib import admin
from .models import Review, ReviewPhoto


class ReviewPhotoInline(admin.TabularInline):
    model = ReviewPhoto
    extra = 1
    fields = ('image', 'caption', 'order')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'rating', 'is_flagged', 'created_at')
    list_filter = ('rating', 'is_flagged', 'created_at')
    search_fields = ('user__username', 'location__name', 'text')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ReviewPhotoInline]
    raw_id_fields = ('user', 'location')


@admin.register(ReviewPhoto)
class ReviewPhotoAdmin(admin.ModelAdmin):
    list_display = ('review', 'caption', 'order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('review__user__username', 'caption')
    raw_id_fields = ('review',)
