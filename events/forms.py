from django import forms
from .models import Event, Invitation, RSVP
from locations.models import Location


class EventForm(forms.ModelForm):
    """Form for creating/editing events"""
    class Meta:
        model = Event
        fields = ['title', 'description', 'visibility', 'start_time', 'end_time', 
                  'max_attendees', 'itinerary']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class InvitationForm(forms.ModelForm):
    """Form for inviting users to events"""
    class Meta:
        model = Invitation
        fields = ['invited_user', 'invited_email', 'role']
        help_texts = {
            'invited_user': 'Select a registered user',
            'invited_email': 'Or enter email for non-registered users',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('invited_user')
        email = cleaned_data.get('invited_email')
        
        if not user and not email:
            raise forms.ValidationError('Please provide either a username or email address.')
        
        return cleaned_data


class RSVPForm(forms.ModelForm):
    """Form for RSVP status"""
    class Meta:
        model = RSVP
        fields = ['status']
        widgets = {
            'status': forms.RadioSelect(),
        }

