from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Report(models.Model):
    """Generic report system for content moderation"""
    REASON_CHOICES = [
        ('inaccurate', 'Inaccurate Information'),
        ('inappropriate', 'Inappropriate Content'),
        ('spam', 'Spam'),
        ('abusive', 'Abusive Behavior'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Reporter
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_filed')
    
    # Reported content (generic)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Report details
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    message = models.TextField(help_text="Details about the issue")
    
    # Moderation
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='reports_reviewed')
    resolution_note = models.TextField(blank=True, help_text="Moderator notes")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report #{self.pk} - {self.get_reason_display()} by {self.reporter.username}"
