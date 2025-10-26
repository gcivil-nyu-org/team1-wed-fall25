from django.db import models


class EventVisibility(models.TextChoices):
    PUBLIC_OPEN = "PUBLIC_OPEN", "Public - Open to All"
    PUBLIC_INVITE = "PUBLIC_INVITE", "Public - Invite Only"
    PRIVATE = "PRIVATE", "Private"


class MembershipRole(models.TextChoices):
    HOST = "HOST", "Host"
    ATTENDEE = "ATTENDEE", "Attendee"
    INVITED = "INVITED", "Invited"


class InviteStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    DECLINED = "DECLINED", "Declined"
    EXPIRED = "EXPIRED", "Expired"


class JoinRequestStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    DECLINED = "DECLINED", "Declined"
