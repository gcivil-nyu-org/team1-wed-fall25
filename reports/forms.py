from django import forms
from .models import Report


class ReportForm(forms.ModelForm):
    """Form for reporting content"""
    class Meta:
        model = Report
        fields = ['reason', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Please describe the issue...'}),
        }

