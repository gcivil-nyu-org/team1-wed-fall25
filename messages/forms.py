from django import forms
from .models import PrivateMessage


class MessageForm(forms.ModelForm):
    """Form for sending a private message"""

    class Meta:
        model = PrivateMessage
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Type your message...",
                    "rows": 3,
                    "maxlength": 2000,
                }
            )
        }

    def clean_content(self):
        content = self.cleaned_data.get("content", "").strip()
        if not content:
            raise forms.ValidationError("Message cannot be empty.")
        return content

