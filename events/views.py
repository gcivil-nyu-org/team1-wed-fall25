from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction

from .models import Event
from .forms import EventForm, parse_locations, parse_invites
from .services import create_event
from .selectors import search_locations, search_users, public_event_pins


@login_required
def create(request):
    """Create a new event"""
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            try:
                locations = parse_locations(request)
                invites = parse_invites(request)
                
                event = create_event(
                    host=request.user,
                    form=form,
                    locations=locations,
                    invites=invites
                )
                
                messages.success(request, f'Event "{event.title}" created successfully!')
                return redirect(event.get_absolute_url())
                
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, 'An error occurred while creating the event.')
    else:
        form = EventForm()
    
    return render(request, 'events/create.html', {'form': form})


@login_required
def detail(request, slug):
    """Event detail page (stub for Phase 1)"""
    event = get_object_or_404(Event, slug=slug)
    return render(request, 'events/detail.html', {'event': event})


@login_required
def api_locations_search(request):
    """JSON API for location autocomplete"""
    term = request.GET.get('q', '').strip()
    
    if not term or len(term) < 2:
        return JsonResponse({'results': []})
    
    locations = search_locations(term, limit=10)
    
    # Return compact format matching map style
    results = [
        {
            'id': loc['id'],
            't': loc['title'] or 'Untitled',
            'a': loc['artist_name'] or 'Unknown',
            'y': float(loc['latitude']),
            'x': float(loc['longitude'])
        }
        for loc in locations
    ]
    
    return JsonResponse({'results': results})


@login_required
def api_users_search(request):
    """JSON API for user autocomplete"""
    term = request.GET.get('q', '').strip()
    
    if not term or len(term) < 2:
        return JsonResponse({'results': []})
    
    users = search_users(term, limit=10)
    
    results = [
        {
            'id': user['id'],
            'u': user['username']
        }
        for user in users
    ]
    
    return JsonResponse({'results': results})


@login_required
def api_event_pins(request):
    """JSON API for event pins on map"""
    events = public_event_pins()
    
    points = [
        {
            'id': event['id'],
            't': event['title'],
            'y': float(event['start_location__latitude']),
            'x': float(event['start_location__longitude']),
            'slug': event['slug']
        }
        for event in events
    ]
    
    return JsonResponse({'points': points})

