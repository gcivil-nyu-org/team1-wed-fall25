from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""

    class Meta:
        model = UserProfile
        fields = ["full_name", "about", "privacy", "profile_image"]
        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Your full name"}
            ),
            "about": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Tell us about yourself...",
                    "maxlength": 500,
                }
            ),
            "privacy": forms.Select(attrs={"class": "form-control"}),
            "profile_image": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                    "id": "profile-image-input",  # Add ID for JavaScript
                }
            ),
        }
        labels = {
            "full_name": "Full Name",
            "about": "About Yourself",
            "privacy": "Profile Privacy",
            "profile_image": "Profile Picture",
        }
        help_texts = {
            "about": "Maximum 500 characters",
            "privacy": "Public profiles can be viewed by anyone",
        }

    def clean_profile_image(self):
        """Validate profile image size"""
        image = self.cleaned_data.get("profile_image")
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Image file too large ( > 5MB )")
        return image


class UserBasicInfoForm(forms.ModelForm):
    """Form for editing basic user information"""

    class Meta:
        model = User
        fields = ["username", "email"]
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "readonly": "readonly"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "your.email@example.com"}
            ),
        }
        help_texts = {
            "username": "Username cannot be changed",
            "email": "Your email address",
        }

    def clean_email(self):
        """Validate email uniqueness (excluding current user)"""
        email = self.cleaned_data.get("email")
        if (
            User.objects.exclude(pk=self.instance.pk)
            .filter(email__iexact=email)
            .exists()
        ):
            raise forms.ValidationError("This email is already in use.")
        return email.lower()
