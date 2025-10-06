# M4: Events with Invitations Complete

## Completed Tasks

### Models
- ✅ Event model with:
  - Owner, title, description
  - visibility (public/restricted/private)
  - Start/end times
  - max_attendees (optional capacity)
  - share_token for link sharing
  - Optional linked itinerary
- ✅ EventLocation model (many-to-many through table)
- ✅ Invitation model with:
  - invited_user OR invited_email
  - Status (pending/accepted/declined)
  - Role (attendee/cohost)
  - Token for accepting
  - Expiration (7 days default)
- ✅ RSVP model (going/maybe/not_going)
- ✅ Admin registration for all models

### Forms
- ✅ EventForm for create/edit
- ✅ InvitationForm for inviting users
- ✅ RSVPForm for status selection

### Views & URLs
- ✅ event_list: public + user's events, filter by time
- ✅ event_detail: full details with visibility checks
  - Shows attendees (going/maybe)
  - RSVP buttons for non-owners
- ✅ event_create/edit: CRUD for events
- ✅ event_delete: owner-only deletion
- ✅ event_invite: send invitations by user or email
  - Email notification sent (console backend)
- ✅ invite_accept: accept invitation via token
  - Auto-creates RSVP
- ✅ event_rsvp: update RSVP status
  - Capacity check

### Templates
- ✅ events/list.html: grid with time filter
- ✅ events/detail.html: full event with RSVP
- ✅ events/form.html: create/edit form
- ✅ events/invite.html: invitation manager

### Visibility System
- ✅ Public: anyone can view and RSVP
- ✅ Restricted: invitation-only, invited users can view
- ✅ Private: owner-only
- ✅ Permission checks in all views

### Invitation System
- ✅ Invite by username OR email
- ✅ Token-based accept link
- ✅ Email notifications (console backend for dev)
- ✅ Expiration tracking (7 days)
- ✅ Status tracking (pending/accepted/declined)

### RSVP System
- ✅ Three states: going, maybe, not_going
- ✅ Capacity enforcement (if max_attendees set)
- ✅ Unique constraint per event+user
- ✅ Attendee list display

## File Structure
```
events/
├── admin.py (4 models)
├── forms.py (EventForm, InvitationForm, RSVPForm)
├── migrations/
│   └── 0001_initial.py
├── models.py (Event, EventLocation, Invitation, RSVP)
├── urls.py (8 routes)
└── views.py (8 views)

templates/events/
├── detail.html
├── form.html
├── invite.html
└── list.html
```

## Database State
- 4 event tables created
- Migrations applied successfully
- Ready for event creation

## Next Steps (M5)
- Create Report model with generic foreign key
- Implement report creation flow
- Admin moderation interface

## Technical Notes
- secrets.token_urlsafe for tokens
- timezone-aware datetime fields
- Email via console backend (dev)
- Visibility enforced at query + view level
- Capacity checks prevent overbooking
- Invitation expiration (7 days default)
- unique_together constraints prevent duplicates

