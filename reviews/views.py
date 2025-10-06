from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from locations.models import Location
from .models import Review, ReviewPhoto
from .forms import ReviewForm, ReviewPhotoFormSet


@login_required
def review_create(request, location_pk):
    """Create a new review for a location"""
    location = get_object_or_404(Location, pk=location_pk, is_active=True)
    
    # Check if user already reviewed
    existing_review = Review.objects.filter(user=request.user, location=location).first()
    if existing_review:
        messages.warning(request, 'You have already reviewed this location. Edit your existing review instead.')
        return redirect('reviews:edit', pk=existing_review.pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        photo_formset = ReviewPhotoFormSet(request.POST, request.FILES)
        
        if form.is_valid() and photo_formset.is_valid():
            with transaction.atomic():
                review = form.save(commit=False)
                review.user = request.user
                review.location = location
                review.save()
                
                # Save photos
                photo_formset.instance = review
                photo_formset.save()
                
            messages.success(request, 'Review posted successfully!')
            return redirect('locations:detail', pk=location.pk)
    else:
        form = ReviewForm()
        photo_formset = ReviewPhotoFormSet()
    
    context = {
        'form': form,
        'photo_formset': photo_formset,
        'location': location,
        'action': 'Create'
    }
    
    return render(request, 'reviews/form.html', context)


@login_required
def review_edit(request, pk):
    """Edit existing review (author only)"""
    review = get_object_or_404(Review, pk=pk)
    
    if review.user != request.user and not request.user.is_staff:
        messages.error(request, 'You can only edit your own reviews.')
        return redirect('locations:detail', pk=review.location.pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        photo_formset = ReviewPhotoFormSet(request.POST, request.FILES, instance=review)
        
        if form.is_valid() and photo_formset.is_valid():
            with transaction.atomic():
                form.save()
                photo_formset.save()
                
            messages.success(request, 'Review updated successfully!')
            return redirect('locations:detail', pk=review.location.pk)
    else:
        form = ReviewForm(instance=review)
        photo_formset = ReviewPhotoFormSet(instance=review)
    
    context = {
        'form': form,
        'photo_formset': photo_formset,
        'location': review.location,
        'review': review,
        'action': 'Edit'
    }
    
    return render(request, 'reviews/form.html', context)


@login_required
def review_delete(request, pk):
    """Delete review (author or staff only)"""
    review = get_object_or_404(Review, pk=pk)
    location_pk = review.location.pk
    
    if review.user != request.user and not request.user.is_staff:
        messages.error(request, 'You can only delete your own reviews.')
        return redirect('locations:detail', pk=location_pk)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted successfully.')
        return redirect('locations:detail', pk=location_pk)
    
    return render(request, 'reviews/delete_confirm.html', {'review': review})
