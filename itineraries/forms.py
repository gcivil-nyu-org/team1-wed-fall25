from django import forms
from .models import Itinerary, ItineraryItem
from locations.models import Location


class ItineraryForm(forms.ModelForm):
    """Form for creating/editing itineraries"""
    class Meta:
        model = Itinerary
        fields = ['title', 'notes', 'is_public']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Notes about this itinerary...'}),
        }


class ItineraryItemForm(forms.ModelForm):
    """Form for adding items to itinerary"""
    class Meta:
        model = ItineraryItem
        fields = ['location', 'note', 'planned_start', 'planned_end']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional note for this stop'}),
            'planned_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'planned_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

