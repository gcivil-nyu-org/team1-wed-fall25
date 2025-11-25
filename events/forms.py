from django import forms
from .models import Event
from .validators import validate_future_datetime
from loc_detail.models import PublicArt


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "start_time", "start_location", "visibility", "description"]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 4, "maxlength": 300}),
            "start_location": forms.Select(attrs={"class": "create-form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate start_location dropdown with all locations
        self.fields["start_location"].queryset = PublicArt.objects.filter(
            latitude__isnull=False, longitude__isnull=False
        ).order_by("title")
        self.fields["start_location"].empty_label = "Select a location..."

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()
        if len(title) > 80:
            raise forms.ValidationError("Title must be 80 characters or less.")
        return title

    def clean_start_time(self):
        start_time = self.cleaned_data.get("start_time")
        if start_time:
            validate_future_datetime(start_time)
        return start_time

    def clean_start_location(self):
        location = self.cleaned_data.get("start_location")
        if location and (not location.latitude or not location.longitude):
            raise forms.ValidationError(
                "Selected location must have valid coordinates."
            )
        return location


def parse_locations(request):
    """Parse locations[] from POST data"""
    locations = request.POST.getlist("locations[]")
    return [int(loc_id) for loc_id in locations if loc_id.isdigit()]


def parse_invites(request):
    """Parse invites[] from POST data"""
    invites = request.POST.getlist("invites[]")
    return [int(user_id) for user_id in invites if user_id.isdigit()]
