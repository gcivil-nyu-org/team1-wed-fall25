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


class MessageReportReason(models.TextChoices):
    INAPPROPRIATE = "INAPPROPRIATE", "Inappropriate content"
    SPAM = "SPAM", "Spam"
    HARASSMENT = "HARASSMENT", "Harassment"
    OFF_TOPIC = "OFF_TOPIC", "Off-topic"
    OTHER = "OTHER", "Other"


class ReportStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Review"
    REVIEWING = "REVIEWING", "Under Review"
    RESOLVED = "RESOLVED", "Resolved"
    DISMISSED = "DISMISSED", "Dismissed"
