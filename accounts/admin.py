from django.contrib import admin
from .models import EmailVerificationOTP


@admin.register(EmailVerificationOTP)
class EmailVerificationOTPAdmin(admin.ModelAdmin):
    list_display = ["email", "username", "otp", "created_at", "is_verified"]
    list_filter = ["is_verified", "created_at"]
    search_fields = ["email", "username"]
    readonly_fields = ["created_at", "otp"]
    ordering = ["-created_at"]
