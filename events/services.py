from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from loc_detail.models import PublicArt

from .models import EventLocation, EventMembership, EventInvite
from .enums import MembershipRole, InviteStatus, EventVisibility
from .validators import validate_max_locations

User = get_user_model()


@transaction.atomic
def create_event(*, host, form, locations, invites):
    """
    Create an event with all related objects

    Args:
        host: User creating the event
        form: Validated EventForm
        locations: List of PublicArt IDs for additional stops
        invites: List of User IDs to invite

    Returns:
        Created Event instance
    """
    # Validate business rules
    validate_max_locations(locations, max_allowed=5)

    # Dedupe locations while preserving order
    seen = set()
    unique_locations = []
    for loc_id in locations:
        if loc_id not in seen:
            seen.add(loc_id)
            unique_locations.append(loc_id)

    # Ensure all location IDs exist
    valid_locations = PublicArt.objects.filter(id__in=unique_locations)
    if valid_locations.count() != len(unique_locations):
        raise ValueError("One or more locations are invalid.")

    # Dedupe invites and exclude host
    unique_invites = list(set(invites) - {host.id})

    # Ensure all invitee IDs exist
    if unique_invites:
        valid_users = User.objects.filter(id__in=unique_invites)
        if valid_users.count() != len(unique_invites):
            raise ValueError("One or more invitees are invalid.")

    # Create event
    event = form.save(commit=False)
    event.host = host
    event.save()

    # Create host membership
    EventMembership.objects.create(event=event, user=host, role=MembershipRole.HOST)

    # Create location stops
    for order, loc_id in enumerate(unique_locations, start=1):
        EventLocation.objects.create(event=event, location_id=loc_id, order=order)

    # Create invites
    for invitee_id in unique_invites:
        EventInvite.objects.create(
            event=event,
            invited_by=host,
            invitee_id=invitee_id,
            status=InviteStatus.PENDING,
        )
        # Also create membership with INVITED role
        EventMembership.objects.create(
            event=event, user_id=invitee_id, role=MembershipRole.INVITED
        )

    return event


@transaction.atomic
def join_event(*, event, user):
    """
    Add user as attendee to event

    Business Rules:
    - PUBLIC_OPEN: Anyone can join
    - PUBLIC_INVITE: Must have pending invite
    - PRIVATE: Not allowed
    - Cannot join if already HOST or ATTENDEE

    Raises:
        ValueError: If join not allowed
    """
    # Check if already joined
    existing = EventMembership.objects.filter(
        event=event, user=user, role__in=[MembershipRole.HOST, MembershipRole.ATTENDEE]
    ).exists()

    if existing:
        raise ValueError("You have already joined this event.")

    # Visibility checks
    if event.visibility == EventVisibility.PRIVATE:
        raise ValueError("This is a private event.")

    if event.visibility == EventVisibility.PUBLIC_INVITE:
        # Must have invite
        has_invite = EventInvite.objects.filter(
            event=event, invitee=user, status=InviteStatus.PENDING
        ).exists()

        if not has_invite:
            raise ValueError("You must be invited to join this event.")

    # Create or update membership
    EventMembership.objects.update_or_create(
        event=event, user=user, defaults={"role": MembershipRole.ATTENDEE}
    )


@transaction.atomic
def accept_invite(*, invite):
    """
    Accept an invitation

    - Updates invite status to ACCEPTED
    - Creates/updates EventMembership to ATTENDEE
    - Sets responded_at timestamp
    """
    invite.status = InviteStatus.ACCEPTED
    invite.responded_at = timezone.now()
    invite.save()

    # Update membership from INVITED to ATTENDEE
    EventMembership.objects.update_or_create(
        event=invite.event,
        user=invite.invitee,
        defaults={"role": MembershipRole.ATTENDEE},
    )


@transaction.atomic
def decline_invite(*, invite):
    """
    Decline an invitation

    - Updates invite status to DECLINED
    - Removes INVITED membership
    - Sets responded_at timestamp
    """
    invite.status = InviteStatus.DECLINED
    invite.responded_at = timezone.now()
    invite.save()

    # Remove invited membership
    EventMembership.objects.filter(
        event=invite.event, user=invite.invitee, role=MembershipRole.INVITED
    ).delete()


# PHASE 3 SERVICES


@transaction.atomic
def post_chat_message(*, event, user, message):
    """
    Post a chat message and enforce 20-message retention

    Business Rules:
    - User must be HOST or ATTENDEE
    - Message length: 1-300 chars
    - Auto-delete oldest messages beyond 20 per event

    Raises:
        ValueError: If user not authorized or message invalid
    """
    from .models import EventChatMessage

    # Check permission
    is_member = EventMembership.objects.filter(
        event=event, user=user, role__in=[MembershipRole.HOST, MembershipRole.ATTENDEE]
    ).exists()

    if not is_member:
        raise ValueError("Only event members can post messages.")

    # Validate message
    message = message.strip()
    if not message or len(message) > 300:
        raise ValueError("Message must be 1-300 characters.")

    # Create message
    EventChatMessage.objects.create(event=event, author=user, message=message)

    # Enforce retention: keep only latest 20 messages
    messages = EventChatMessage.objects.filter(event=event).order_by("-created_at")
    if messages.count() > 20:
        old_messages = messages[20:]
        EventChatMessage.objects.filter(id__in=[m.id for m in old_messages]).delete()


@transaction.atomic
def request_join(*, event, user):
    """
    Create a join request for PUBLIC_INVITE event

    Business Rules:
    - Only for PUBLIC_INVITE events
    - User must not already be member or invited
    - Idempotent: no-op if request exists

    Raises:
        ValueError: If not allowed
    """
    from .models import EventJoinRequest, EventInvite
    from .enums import JoinRequestStatus

    # Check event visibility
    if event.visibility != EventVisibility.PUBLIC_INVITE:
        raise ValueError("Join requests only allowed for invite-only events.")

    # Check if already member
    is_member = EventMembership.objects.filter(event=event, user=user).exists()

    if is_member:
        raise ValueError("You are already a member of this event.")

    # Check if already invited
    has_invite = EventInvite.objects.filter(
        event=event, invitee=user, status=InviteStatus.PENDING
    ).exists()

    if has_invite:
        raise ValueError("You already have an invitation to this event.")

    # Create request (idempotent)
    EventJoinRequest.objects.get_or_create(
        event=event, requester=user, defaults={"status": JoinRequestStatus.PENDING}
    )


@transaction.atomic
def approve_join_request(*, join_request):
    """
    Approve a join request and add user as attendee

    - Updates request status to APPROVED
    - Creates EventMembership with ATTENDEE role
    - Sets decided_at timestamp
    """
    from .enums import JoinRequestStatus

    join_request.status = JoinRequestStatus.APPROVED
    join_request.decided_at = timezone.now()
    join_request.save()

    # Add user as attendee
    EventMembership.objects.get_or_create(
        event=join_request.event,
        user=join_request.requester,
        defaults={"role": MembershipRole.ATTENDEE},
    )


@transaction.atomic
def decline_join_request(*, join_request):
    """
    Decline a join request

    - Updates request status to DECLINED
    - Sets decided_at timestamp
    """
    from .enums import JoinRequestStatus

    join_request.status = JoinRequestStatus.DECLINED
    join_request.decided_at = timezone.now()
    join_request.save()


@transaction.atomic
def update_event(*, event, form, locations, invites):
    """
    Update an existing event

    Args:
        event: Event instance to update
        form: Validated EventForm with new data
        locations: List of PublicArt IDs for additional stops
        invites: List of User IDs to invite

    Returns:
        Updated Event instance
    """
    # Validate business rules
    validate_max_locations(locations, max_allowed=5)

    # Dedupe locations while preserving order
    seen = set()
    unique_locations = []
    for loc_id in locations:
        if loc_id not in seen:
            seen.add(loc_id)
            unique_locations.append(loc_id)

    # Ensure all location IDs exist
    valid_locations = PublicArt.objects.filter(id__in=unique_locations)
    if valid_locations.count() != len(unique_locations):
        raise ValueError("One or more locations are invalid.")

    # Dedupe invites and exclude host
    unique_invites = list(set(invites) - {event.host.id})

    # Ensure all invitee IDs exist
    if unique_invites:
        valid_users = User.objects.filter(id__in=unique_invites)
        if valid_users.count() != len(unique_invites):
            raise ValueError("One or more invitees are invalid.")

    # Update event fields
    event.title = form.cleaned_data["title"]
    event.start_time = form.cleaned_data["start_time"]
    event.start_location = form.cleaned_data["start_location"]
    event.visibility = form.cleaned_data["visibility"]
    event.description = form.cleaned_data.get("description", "")
    event.save()

    # Update location stops (clear and recreate)
    EventLocation.objects.filter(event=event).delete()
    for order, loc_id in enumerate(unique_locations, start=1):
        EventLocation.objects.create(event=event, location_id=loc_id, order=order)

    # Update invites (only add new ones, don't remove existing)
    existing_invitees = set(
        EventInvite.objects.filter(event=event).values_list("invitee_id", flat=True)
    )
    new_invitees = set(unique_invites) - existing_invitees

    for invitee_id in new_invitees:
        EventInvite.objects.create(
            event=event,
            invited_by=event.host,
            invitee_id=invitee_id,
            status=InviteStatus.PENDING,
        )
        # Also create membership with INVITED role if not already member
        EventMembership.objects.get_or_create(
            event=event, user_id=invitee_id, defaults={"role": MembershipRole.INVITED}
        )

    return event


@transaction.atomic
def delete_event(*, event):
    """
    Soft delete an event (mark as deleted)

    Args:
        event: Event instance to delete

    Returns:
        Updated Event instance
    """
    event.is_deleted = True
    event.save()
    return event


@transaction.atomic
def leave_event(*, event, user):
    """
    Remove user from event (attendee deregistration)

    Business Rules:
    - User must be an ATTENDEE (not HOST)
    - Removes EventMembership

    Raises:
        ValueError: If user is host or not a member
    """
    if event.host == user:
        raise ValueError("Host cannot leave their own event.")

    # Check if user is an attendee
    membership = EventMembership.objects.filter(
        event=event, user=user, role=MembershipRole.ATTENDEE
    ).first()

    if not membership:
        raise ValueError("You are not registered for this event.")

    # Remove membership
    membership.delete()


@transaction.atomic
def favorite_event(*, event, user):
    """
    Add event to user's favorites

    Business Rules:
    - Idempotent: no-op if already favorited
    - Cannot favorite deleted events

    Raises:
        ValueError: If event is deleted
    """
    from .models import EventFavorite

    if event.is_deleted:
        raise ValueError("Cannot favorite a deleted event.")

    # Create favorite (idempotent)
    EventFavorite.objects.get_or_create(event=event, user=user)


@transaction.atomic
def unfavorite_event(*, event, user):
    """
    Remove event from user's favorites

    Returns:
        bool: True if favorite was removed, False if it didn't exist
    """
    from .models import EventFavorite

    deleted_count, _ = EventFavorite.objects.filter(event=event, user=user).delete()
    return deleted_count > 0
