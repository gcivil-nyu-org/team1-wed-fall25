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
        fields = ["title", "description", "date"]
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
            "date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "placeholder": "Select planned date (optional)",
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
            "order": forms.HiddenInput(
                attrs={
                    "class": "order-field",
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

    def validate_unique(self):
        """
        Skip unique_together validation for (itinerary, order).
        The view handles ordering by deleting all stops and recreating them.
        """
        exclude = self._get_validation_exclusions()
        # Exclude 'order' from unique validation since we handle it manually
        exclude.add("order")
        try:
            self.instance.validate_unique(exclude=exclude)
        except forms.ValidationError as e:
            self._update_errors(e)


# Custom formset that skips unique_together validation for order field
# (since we delete all stops and recreate them with new order values)
class BaseItineraryStopFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        # Skip the unique_together validation that Django does automatically
        # We handle ordering manually by deleting and recreating stops


# Formset for managing multiple stops
ItineraryStopFormSet = inlineformset_factory(
    Itinerary,
    ItineraryStop,
    form=ItineraryStopForm,
    formset=BaseItineraryStopFormSet,
    extra=0,  # Don't show extra empty forms (min_num will handle the minimum)
    can_delete=True,
    min_num=1,  # Show and require at least 1 stop
    validate_min=True,
)
