from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.core.paginator import Paginator
import json
from .models import Itinerary, ItineraryItem
from .forms import ItineraryForm, ItineraryItemForm
from locations.models import Location


@login_required
def itinerary_list(request):
    """List user's itineraries"""
    itineraries = Itinerary.objects.filter(owner=request.user).prefetch_related('items__location')
    
    paginator = Paginator(itineraries, 20)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    
    context = {
        'page_obj': page_obj,
        'itineraries': page_obj.object_list,
    }
    
    return render(request, 'itineraries/list.html', context)


@login_required
def itinerary_detail(request, pk):
    """View itinerary details"""
    itinerary = get_object_or_404(
        Itinerary.objects.prefetch_related('items__location'),
        pk=pk
    )
    
    # Check permissions
    if itinerary.owner != request.user and not itinerary.is_public and not request.user.is_staff:
        messages.error(request, 'You do not have permission to view this itinerary.')
        return redirect('itineraries:list')
    
    items = itinerary.get_ordered_items()
    is_owner = itinerary.owner == request.user
    
    context = {
        'itinerary': itinerary,
        'items': items,
        'is_owner': is_owner,
    }
    
    return render(request, 'itineraries/detail.html', context)


@login_required
def itinerary_create(request):
    """Create new itinerary"""
    if request.method == 'POST':
        form = ItineraryForm(request.POST)
        if form.is_valid():
            itinerary = form.save(commit=False)
            itinerary.owner = request.user
            itinerary.save()
            messages.success(request, f'Itinerary "{itinerary.title}" created!')
            return redirect('itineraries:detail', pk=itinerary.pk)
    else:
        form = ItineraryForm()
    
    return render(request, 'itineraries/form.html', {'form': form, 'action': 'Create'})


@login_required
def itinerary_edit(request, pk):
    """Edit itinerary (owner only)"""
    itinerary = get_object_or_404(Itinerary, pk=pk)
    
    if itinerary.owner != request.user:
        messages.error(request, 'You can only edit your own itineraries.')
        return redirect('itineraries:detail', pk=pk)
    
    if request.method == 'POST':
        form = ItineraryForm(request.POST, instance=itinerary)
        if form.is_valid():
            form.save()
            messages.success(request, f'Itinerary "{itinerary.title}" updated!')
            return redirect('itineraries:detail', pk=itinerary.pk)
    else:
        form = ItineraryForm(instance=itinerary)
    
    return render(request, 'itineraries/form.html', {
        'form': form,
        'action': 'Edit',
        'itinerary': itinerary
    })


@login_required
@require_POST
def itinerary_delete(request, pk):
    """Delete itinerary (owner only)"""
    itinerary = get_object_or_404(Itinerary, pk=pk)
    
    if itinerary.owner != request.user:
        messages.error(request, 'You can only delete your own itineraries.')
        return redirect('itineraries:detail', pk=pk)
    
    title = itinerary.title
    itinerary.delete()
    messages.success(request, f'Itinerary "{title}" deleted.')
    return redirect('itineraries:list')


@login_required
def itinerary_item_add(request, pk):
    """Add item to itinerary"""
    itinerary = get_object_or_404(Itinerary, pk=pk)
    
    if itinerary.owner != request.user:
        messages.error(request, 'You can only add items to your own itineraries.')
        return redirect('itineraries:detail', pk=pk)
    
    if request.method == 'POST':
        form = ItineraryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.itinerary = itinerary
            
            # Set order_index to last
            max_order = itinerary.items.aggregate(models.Max('order_index'))['order_index__max']
            item.order_index = (max_order or 0) + 1
            
            item.save()
            messages.success(request, f'Added "{item.location.name}" to itinerary.')
            return redirect('itineraries:detail', pk=pk)
    else:
        # Pre-fill location if provided
        location_id = request.GET.get('location_id')
        initial = {}
        if location_id:
            try:
                location = Location.objects.get(pk=location_id, is_active=True)
                initial['location'] = location
            except Location.DoesNotExist:
                pass
        
        form = ItineraryItemForm(initial=initial)
    
    context = {
        'form': form,
        'itinerary': itinerary,
    }
    
    return render(request, 'itineraries/item_form.html', context)


@login_required
@require_POST
def itinerary_item_reorder(request, pk):
    """Reorder items via AJAX"""
    itinerary = get_object_or_404(Itinerary, pk=pk)
    
    if itinerary.owner != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        item_ids = data.get('item_ids', [])
        
        with transaction.atomic():
            for index, item_id in enumerate(item_ids):
                ItineraryItem.objects.filter(
                    pk=item_id,
                    itinerary=itinerary
                ).update(order_index=index)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def itinerary_item_delete(request, itinerary_pk, item_pk):
    """Delete item from itinerary"""
    itinerary = get_object_or_404(Itinerary, pk=itinerary_pk)
    item = get_object_or_404(ItineraryItem, pk=item_pk, itinerary=itinerary)
    
    if itinerary.owner != request.user:
        messages.error(request, 'Permission denied.')
        return redirect('itineraries:detail', pk=itinerary_pk)
    
    location_name = item.location.name
    item.delete()
    messages.success(request, f'Removed "{location_name}" from itinerary.')
    return redirect('itineraries:detail', pk=itinerary_pk)


# Import models for aggregation
from django.db import models
