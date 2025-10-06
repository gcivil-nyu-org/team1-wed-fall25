from django import forms
from .models import Location


class LocationForm(forms.ModelForm):
    """Form for creating/editing locations"""
    class Meta:
        model = Location
        fields = [
            'name', 'description', 'address', 'city', 'state', 
            'postal_code', 'latitude', 'longitude', 'website_url', 
            'image_url', 'tags'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'latitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001'}),
        }
        help_texts = {
            'latitude': 'Click on map or enter manually',
            'longitude': 'Click on map or enter manually',
            'image_url': 'URL to an image of this location',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        lat = cleaned_data.get('latitude')
        lng = cleaned_data.get('longitude')
        
        if lat and (lat < -90 or lat > 90):
            raise forms.ValidationError('Latitude must be between -90 and 90')
        if lng and (lng < -180 or lng > 180):
            raise forms.ValidationError('Longitude must be between -180 and 180')
        
        return cleaned_data

