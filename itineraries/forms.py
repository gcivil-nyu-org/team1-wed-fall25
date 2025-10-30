"""
Forms for the itineraries app
"""

from django import forms
from django.forms import inlineformset_factory
from .models import Itinerary, ItineraryStop


class ItineraryForm(forms.ModelForm):
    """Form for creating and editing itineraries"""

    class Meta:
        model = Itinerary
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter itinerary title",
                    "maxlength": "200",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Add a description (optional)",
                    "rows": "3",
                }
            ),
        }


class ItineraryStopForm(forms.ModelForm):
    """Form for adding/editing stops in an itinerary"""

    class Meta:
        model = ItineraryStop
        fields = ["location", "visit_time", "order", "notes"]
        widgets = {
            "location": forms.Select(
                attrs={
                    "class": "form-select location-select",
                    "required": True,
                }
            ),
            "visit_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                    "required": False,
                }
            ),
            "order": forms.NumberInput(
                attrs={
                    "class": "form-control order-input",
                    "min": "1",
                    "required": True,
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Add notes for this stop (optional)",
                    "rows": "2",
                }
            ),
        }


# Formset for managing multiple stops
ItineraryStopFormSet = inlineformset_factory(
    Itinerary,
    ItineraryStop,
    form=ItineraryStopForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
