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
