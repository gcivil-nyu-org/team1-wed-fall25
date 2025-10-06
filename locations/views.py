from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Location, Tag, Favorite
from .forms import LocationForm


def location_list(request):
    """List/map view of locations with filters"""
    locations = Location.objects.filter(is_active=True).select_related('created_by').prefetch_related('tags')
    
    # Search
    q = request.GET.get('q', '')
    if q:
        locations = locations.filter(
            Q(name__icontains=q) | 
            Q(description__icontains=q) |
            Q(address__icontains=q)
        )
    
    # Tag filter
    tag_slug = request.GET.get('tag', '')
    if tag_slug:
        locations = locations.filter(tags__slug=tag_slug)
    
    # Bounding box filter for map viewport
    min_lat = request.GET.get('min_lat')
    max_lat = request.GET.get('max_lat')
    min_lng = request.GET.get('min_lng')
    max_lng = request.GET.get('max_lng')
    
    if all([min_lat, max_lat, min_lng, max_lng]):
        locations = locations.filter(
            latitude__gte=min_lat,
            latitude__lte=max_lat,
            longitude__gte=min_lng,
            longitude__lte=max_lng
        )
    
    # Sort
    sort = request.GET.get('sort', '-created_at')
    if sort in ['-average_rating', '-review_count', '-created_at', 'name']:
        locations = locations.order_by(sort)
    
    # Pagination
    paginator = Paginator(locations, 20)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    
    # All tags for filter
    tags = Tag.objects.all()
    
    # Check if user has favorited (if authenticated)
    user_favorites = set()
    if request.user.is_authenticated:
        user_favorites = set(
            Favorite.objects.filter(user=request.user).values_list('location_id', flat=True)
        )
    
    context = {
        'page_obj': page_obj,
        'locations': page_obj.object_list,
        'tags': tags,
        'current_tag': tag_slug,
        'search_query': q,
        'sort': sort,
        'user_favorites': user_favorites,
    }
    
    return render(request, 'locations/list.html', context)


def location_detail(request, pk):
    """Location detail page"""
    location = get_object_or_404(
        Location.objects.select_related('created_by').prefetch_related('tags'),
        pk=pk,
        is_active=True
    )
    
    # Get reviews
    from reviews.models import Review
    reviews = Review.objects.filter(location=location).select_related('user').prefetch_related('photos')[:10]
    
    # Check if favorited
    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, location=location).exists()
    
    context = {
        'location': location,
        'reviews': reviews,
        'is_favorited': is_favorited,
    }
    
    return render(request, 'locations/detail.html', context)


@login_required
def location_create(request):
    """Create new location"""
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.created_by = request.user
            location.source = 'user'
            location.save()
            form.save_m2m()  # Save tags
            messages.success(request, f'Location "{location.name}" created successfully!')
            return redirect('locations:detail', pk=location.pk)
    else:
        form = LocationForm()
    
    return render(request, 'locations/form.html', {'form': form, 'action': 'Create'})


@login_required
def location_edit(request, pk):
    """Edit location (owner or staff only)"""
    location = get_object_or_404(Location, pk=pk)
    
    if location.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this location.')
        return redirect('locations:detail', pk=pk)
    
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, f'Location "{location.name}" updated successfully!')
            return redirect('locations:detail', pk=location.pk)
    else:
        form = LocationForm(instance=location)
    
    return render(request, 'locations/form.html', {
        'form': form,
        'action': 'Edit',
        'location': location
    })


@login_required
@require_POST
def location_favorite_toggle(request, pk):
    """Toggle favorite status"""
    location = get_object_or_404(Location, pk=pk, is_active=True)
    
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        location=location
    )
    
    if not created:
        favorite.delete()
        favorited = False
        messages.success(request, f'Removed "{location.name}" from favorites.')
    else:
        favorited = True
        messages.success(request, f'Added "{location.name}" to favorites!')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'favorited': favorited})
    
    # Redirect for form submission
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', 'locations:list'))
    return redirect(next_url)


@login_required
def favorites_list(request):
    """List user's favorite locations"""
    favorites = Favorite.objects.filter(user=request.user).select_related('location').prefetch_related('location__tags')
    
    paginator = Paginator(favorites, 20)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    
    context = {
        'page_obj': page_obj,
        'favorites': page_obj.object_list,
    }
    
    return render(request, 'locations/favorites.html', context)
