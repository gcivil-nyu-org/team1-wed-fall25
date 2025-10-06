from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'reason', 'status', 'severity', 'content_type', 'created_at')
    list_filter = ('status', 'severity', 'reason', 'content_type', 'created_at')
    search_fields = ('reporter__username', 'message', 'resolution_note')
    readonly_fields = ('reporter', 'content_type', 'object_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Report Info', {
            'fields': ('reporter', 'content_type', 'object_id', 'reason', 'message', 'created_at')
        }),
        ('Moderation', {
            'fields': ('status', 'severity', 'reviewed_by', 'resolution_note', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if change and not obj.reviewed_by:
            obj.reviewed_by = request.user
        super().save_model(request, obj, form, change)
