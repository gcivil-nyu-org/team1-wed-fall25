from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.urls import reverse

from .models import Event, EventInvite
from .forms import EventForm, parse_locations, parse_invites
from .services import create_event, join_event as join_event_service, accept_invite as accept_invite_service, decline_invite as decline_invite_service
from .selectors import search_locations, search_users, public_event_pins, list_public_events, user_has_joined, list_user_invitations
from .enums import InviteStatus


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
            except ValidationError as e:
                # Show the actual validation error message
                error_msg = e.message if hasattr(e, 'message') else str(e)
                messages.error(request, error_msg)
            except Exception as e:
                # Show the specific error during development
                messages.error(request, f'An error occurred: {str(e)}')
    else:
        form = EventForm()
    
    return render(request, 'events/create.html', {'form': form})


@login_required
def detail(request, slug):
    """Event detail page (stub for Phase 1)"""
    event = get_object_or_404(Event, slug=slug)
    return render(request, 'events/detail.html', {'event': event})


@login_required
def index(request):
    """Redirect to public events as default"""
    return redirect('events:public')


@login_required
def public_events(request):
    """Display public events with search, filter, and pagination"""
    # Parse query params
    query = request.GET.get('q', '').strip()
    visibility_filter = request.GET.get('filter', '')  # 'open' or 'invite'
    sort = request.GET.get('sort', 'start_time')  # 'start_time' or '-start_time'
    
    # Get events
    events = list_public_events(
        query=query if query else None,
        visibility_filter=visibility_filter if visibility_filter else None,
        order=sort
    )
    
    # Add 'joined' attribute to each event
    events_list = []
    for event in events:
        event.joined = user_has_joined(event, request.user)
        events_list.append(event)
    
    # Pagination
    paginator = Paginator(events_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'filter': visibility_filter,
        'sort': sort,
    }
    
    return render(request, 'events/public_events.html', context)


@login_required
@require_POST
def join_event(request, slug):
    """Join a public event"""
    event = get_object_or_404(Event, slug=slug)
    
    try:
        join_event_service(event=event, user=request.user)
        messages.success(request, f'You have joined "{event.title}"!')
    except ValueError as e:
        messages.error(request, str(e))
    
    # Redirect back to public events with query params preserved
    redirect_url = reverse('events:public')
    query_params = request.GET.urlencode()
    if query_params:
        redirect_url += f'?{query_params}'
    
    return redirect(redirect_url)


@login_required
def invitations(request):
    """Display pending invitations for current user"""
    invites = list_user_invitations(request.user)
    
    return render(request, 'events/invitations.html', {
        'invites': invites
    })


@login_required
@require_POST
def accept_invite(request, slug):
    """Accept an invitation"""
    event = get_object_or_404(Event, slug=slug)
    invite = get_object_or_404(
        EventInvite,
        event=event,
        invitee=request.user,
        status=InviteStatus.PENDING
    )
    
    try:
        accept_invite_service(invite=invite)
        messages.success(request, f'You have accepted the invitation to "{event.title}"!')
        return redirect(event.get_absolute_url())
    except Exception as e:
        messages.error(request, 'Failed to accept invitation.')
        return redirect('events:invitations')


@login_required
@require_POST
def decline_invite(request, slug):
    """Decline an invitation"""
    event = get_object_or_404(Event, slug=slug)
    invite = get_object_or_404(
        EventInvite,
        event=event,
        invitee=request.user,
        status=InviteStatus.PENDING
    )
    
    try:
        decline_invite_service(invite=invite)
        messages.success(request, 'Invitation declined.')
    except Exception as e:
        messages.error(request, 'Failed to decline invitation.')
    
    return redirect('events:invitations')


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

