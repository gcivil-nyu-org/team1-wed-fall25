from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string


class EmailVerificationOTP(models.Model):
    """Model to store OTP for email verification"""

    email = models.EmailField()
    username = models.CharField(max_length=150)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    password_hash = models.CharField(max_length=255)  # Store hashed password

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP for {self.email}"

    def is_expired(self):
        """Check if OTP is expired (3 minutes)"""
        expiry_time = self.created_at + timedelta(minutes=3)
        return timezone.now() > expiry_time

    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP"""
        return "".join(random.choices(string.digits, k=6))

    def save(self, *args, **kwargs):
        if not self.otp:
            self.otp = self.generate_otp()
        super().save(*args, **kwargs)
