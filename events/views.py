from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Event, EventLocation, Invitation, RSVP
from .forms import EventForm, InvitationForm, RSVPForm
from locations.models import Location


def event_list(request):
    """List public events and user's events"""
    if request.user.is_authenticated:
        # Show public events + user's own events
        events = Event.objects.filter(
            Q(visibility='public', is_active=True) |
            Q(owner=request.user, is_active=True)
        ).select_related('owner').prefetch_related('locations').distinct()
    else:
        # Anonymous users see only public events
        events = Event.objects.filter(visibility='public', is_active=True).select_related('owner').prefetch_related('locations')
    
    # Filter by upcoming/past
    filter_time = request.GET.get('time', 'upcoming')
    now = timezone.now()
    if filter_time == 'upcoming':
        events = events.filter(start_time__gte=now)
    elif filter_time == 'past':
        events = events.filter(start_time__lt=now)
    
    events = events.order_by('start_time')
    
    paginator = Paginator(events, 20)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)
    
    context = {
        'page_obj': page_obj,
        'events': page_obj.object_list,
        'filter_time': filter_time,
    }
    
    return render(request, 'events/list.html', context)


def event_detail(request, pk):
    """Event detail page"""
    event = get_object_or_404(
        Event.objects.select_related('owner', 'itinerary').prefetch_related('locations__location', 'rsvps'),
        pk=pk
    )
    
    # Check visibility
    can_view = (
        event.visibility == 'public' or
        event.owner == request.user or
        request.user.is_staff or
        (request.user.is_authenticated and event.invitations.filter(invited_user=request.user).exists())
    )
    
    if not can_view:
        messages.error(request, 'This event is private.')
        return redirect('events:list')
    
    # Get RSVPs
    rsvps_going = event.rsvps.filter(status='going').select_related('user')
    rsvps_maybe = event.rsvps.filter(status='maybe').select_related('user')
    
    # Check user's RSVP
    user_rsvp = None
    if request.user.is_authenticated:
        user_rsvp = event.rsvps.filter(user=request.user).first()
    
    is_owner = request.user.is_authenticated and event.owner == request.user
    
    context = {
        'event': event,
        'locations': event.locations.all(),
        'rsvps_going': rsvps_going,
        'rsvps_maybe': rsvps_maybe,
        'user_rsvp': user_rsvp,
        'is_owner': is_owner,
        'is_full': event.is_full(),
    }
    
    return render(request, 'events/detail.html', context)


@login_required
def event_create(request):
    """Create new event"""
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.owner = request.user
            event.save()
            messages.success(request, f'Event "{event.title}" created!')
            return redirect('events:detail', pk=event.pk)
    else:
        form = EventForm()
    
    return render(request, 'events/form.html', {'form': form, 'action': 'Create'})


@login_required
def event_edit(request, pk):
    """Edit event (owner only)"""
    event = get_object_or_404(Event, pk=pk)
    
    if event.owner != request.user:
        messages.error(request, 'You can only edit your own events.')
        return redirect('events:detail', pk=pk)
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f'Event "{event.title}" updated!')
            return redirect('events:detail', pk=pk)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/form.html', {
        'form': form,
        'action': 'Edit',
        'event': event
    })


@login_required
@require_POST
def event_delete(request, pk):
    """Delete event (owner only)"""
    event = get_object_or_404(Event, pk=pk)
    
    if event.owner != request.user:
        messages.error(request, 'You can only delete your own events.')
        return redirect('events:detail', pk=pk)
    
    title = event.title
    event.delete()
    messages.success(request, f'Event "{title}" deleted.')
    return redirect('events:list')


@login_required
def event_invite(request, pk):
    """Invite users to event (owner only)"""
    event = get_object_or_404(Event, pk=pk)
    
    if event.owner != request.user:
        messages.error(request, 'Only the event owner can send invitations.')
        return redirect('events:detail', pk=pk)
    
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.event = event
            invitation.inviter = request.user
            invitation.save()
            
            # Send email notification
            if invitation.invited_user:
                target = invitation.invited_user.email
                username = invitation.invited_user.username
            else:
                target = invitation.invited_email
                username = invitation.invited_email
            
            if target:
                try:
                    send_mail(
                        subject=f'Invitation to {event.title}',
                        message=f'You have been invited to {event.title}.\n\nAccept: {request.build_absolute_uri("/events/invites/" + invitation.token + "/accept/")}',
                        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@artinerary.com',
                        recipient_list=[target],
                        fail_silently=True,
                    )
                except:
                    pass
            
            messages.success(request, f'Invitation sent to {username}!')
            return redirect('events:detail', pk=pk)
    else:
        form = InvitationForm()
    
    # Show existing invitations
    invitations = event.invitations.select_related('invited_user').order_by('-created_at')
    
    context = {
        'form': form,
        'event': event,
        'invitations': invitations,
    }
    
    return render(request, 'events/invite.html', context)


@login_required
def invite_accept(request, token):
    """Accept event invitation via token"""
    invitation = get_object_or_404(Invitation, token=token)
    
    if invitation.is_expired():
        messages.error(request, 'This invitation has expired.')
        return redirect('events:list')
    
    if invitation.status != 'pending':
        messages.info(request, 'This invitation has already been responded to.')
        return redirect('events:detail', pk=invitation.event.pk)
    
    # Update invitation
    invitation.status = 'accepted'
    invitation.save()
    
    # Create RSVP
    RSVP.objects.get_or_create(
        event=invitation.event,
        user=request.user,
        defaults={'status': 'going'}
    )
    
    messages.success(request, f'You have joined "{invitation.event.title}"!')
    return redirect('events:detail', pk=invitation.event.pk)


@login_required
@require_POST
def event_rsvp(request, pk):
    """RSVP to event"""
    event = get_object_or_404(Event, pk=pk, is_active=True)
    
    # Check if event is viewable
    can_rsvp = (
        event.visibility == 'public' or
        event.owner == request.user or
        event.invitations.filter(invited_user=request.user, status='accepted').exists()
    )
    
    if not can_rsvp:
        messages.error(request, 'You cannot RSVP to this event.')
        return redirect('events:list')
    
    # Check capacity
    if event.is_full() and not RSVP.objects.filter(event=event, user=request.user).exists():
        messages.error(request, 'This event is full.')
        return redirect('events:detail', pk=pk)
    
    status = request.POST.get('status', 'going')
    if status not in ['going', 'maybe', 'not_going']:
        status = 'going'
    
    rsvp, created = RSVP.objects.update_or_create(
        event=event,
        user=request.user,
        defaults={'status': status}
    )
    
    if status == 'going':
        messages.success(request, f'You are going to "{event.title}"!')
    elif status == 'maybe':
        messages.success(request, 'RSVP updated to Maybe.')
    else:
        messages.success(request, 'RSVP updated to Not Going.')
    
    return redirect('events:detail', pk=pk)
