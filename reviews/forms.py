from django import forms
from .models import Review, ReviewPhoto


class ReviewForm(forms.ModelForm):
    """Form for creating/editing reviews"""
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f'{i} ⭐') for i in range(1, 6)]),
            'text': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Share your experience...'}),
        }


class ReviewPhotoForm(forms.ModelForm):
    """Form for adding photos to reviews"""
    class Meta:
        model = ReviewPhoto
        fields = ['image', 'caption']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Optional caption'}),
        }


# Formset for multiple photos
ReviewPhotoFormSet = forms.inlineformset_factory(
    Review,
    ReviewPhoto,
    form=ReviewPhotoForm,
    extra=3,
    max_num=5,
    can_delete=True
)

