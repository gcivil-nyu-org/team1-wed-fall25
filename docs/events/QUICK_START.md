# Events Feature - Quick Start Guide

## For the Next Developer

This guide helps you understand and continue development of the Events feature.

## What's Done (Phase 1) ✅

1. **Complete database schema** for all 3 phases (6 models)
2. **Create Event page** with autocomplete and dynamic chips
3. **Event detail page** (stub for now)
4. **Map integration** with purple event pins
5. **Admin interface** for managing events
6. **Comprehensive tests** for models and services

## How to Run

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run server
python manage.py runserver

# Navigate to:
# - Create Event: http://localhost:8000/events/create/
# - Map with events: http://localhost:8000/artinerary/
# - Admin: http://localhost:8000/admin/
```

## Key Files to Know

### Backend (Django)
- `events/models.py` - 6 models (Event, EventLocation, EventMembership, EventInvite, EventChatMessage, EventJoinRequest)
- `events/enums.py` - Choice classes (EventVisibility, MembershipRole, InviteStatus, JoinRequestStatus)
- `events/selectors.py` - Read-only queries (search_locations, search_users, public_event_pins)
- `events/services.py` - Write operations (create_event)
- `events/forms.py` - EventForm with validation
- `events/views.py` - Views and JSON APIs
- `events/urls.py` - URL patterns

### Frontend (Django Templates + Vanilla JS)
- `events/templates/events/create.html` - Create event form
- `events/templates/events/detail.html` - Event detail (stub)
- `events/static/events/create.js` - Autocomplete and dynamic chips
- `static/js/map/events.js` - Event markers on map

### Tests
- `events/tests.py` - Model, service, and form tests

## Code Architecture

### Modular Pattern (Django Best Practice)
```
User Request
    ↓
View (thin controller)
    ↓
Service (business logic) ← calls → Selector (read data)
    ↓                                    ↓
Model (database)                    Model (database)
```

**Rules:**
- **Selectors** = READ-ONLY, no side effects, can be cached
- **Services** = WRITE operations, use `@transaction.atomic`, contain business logic
- **Views** = Thin controllers, just parse input → call service/selector → render template
- **Forms** = Validation only, no business logic

### Why This Pattern?
- **Testable**: Services and selectors are pure functions
- **Reusable**: Phase 2 and 3 will reuse selectors/services
- **Maintainable**: Clear separation of concerns
- **Scalable**: Easy to add new features

## API Endpoints

### For Users (HTML)
- `GET /events/create/` - Create event form
- `POST /events/create/` - Submit event
- `GET /events/<slug>/` - Event detail

### For JavaScript (JSON)
- `GET /events/api/locations/search/?q=<term>` - Location autocomplete
- `GET /events/api/users/search/?q=<term>` - User autocomplete
- `GET /events/api/pins/` - Event pins for map

### JSON Format (Compact)
```json
// Locations
{"results": [{"id": 1, "t": "Title", "a": "Artist", "y": 40.7, "x": -73.9}]}

// Users
{"results": [{"id": 1, "u": "username"}]}

// Event pins
{"points": [{"id": 1, "t": "Event Title", "y": 40.7, "x": -73.9, "slug": "event-slug"}]}
```

## What to Build Next (Phase 2)

### Events Tab Page
1. **Public Events List** - Browse all public events
2. **Invitations List** - See events you're invited to
3. **Join/Accept/Decline Actions** - Interact with events

### Files to Create/Modify:
- `events/selectors.py` - Add:
  - `list_public_events(query, visibility_filter, order)`
  - `list_user_invitations(user)`
  - `user_has_joined(event, user)`

- `events/services.py` - Add:
  - `join_event(event, user)` - Add user as ATTENDEE
  - `accept_invite(invite)` - Change INVITED → ATTENDEE
  - `decline_invite(invite)` - Mark as DECLINED

- `events/views.py` - Add:
  - `public_events(request)` - List public events
  - `invitations(request)` - List user invitations
  - `join_event(request, slug)` - POST to join
  - `accept_invite(request, slug)` - POST to accept
  - `decline_invite(request, slug)` - POST to decline

- `events/urls.py` - Add routes
- `events/templates/events/` - Add:
  - `public_events.html`
  - `invitations.html`
  - `base_tabs.html` (shared header with tabs)

## Database Schema Quick Reference

### Event (Core)
- `slug` (unique, indexed, auto-generated)
- `title` (max 80 chars)
- `host` (FK → User)
- `visibility` (PUBLIC_OPEN, PUBLIC_INVITE, PRIVATE)
- `start_time` (indexed)
- `start_location` (FK → PublicArt)
- `description` (text, optional)

### EventLocation (0-5 additional stops)
- `event` (FK)
- `location` (FK → PublicArt)
- `order` (1-5)

### EventMembership (Who's in the event)
- `event` (FK)
- `user` (FK)
- `role` (HOST, ATTENDEE, INVITED)

### EventInvite (Invitation tracking)
- `event` (FK)
- `invitee` (FK → User)
- `status` (PENDING, ACCEPTED, DECLINED, EXPIRED)

### EventChatMessage (Phase 3)
- Ready but unused in Phase 1

### EventJoinRequest (Phase 3)
- Ready but unused in Phase 1

## Common Tasks

### Add a new selector (read-only query)
```python
# events/selectors.py
def my_new_selector(param):
    """Description of what this query does"""
    from .models import Event
    return Event.objects.filter(...).values(...)
```

### Add a new service (write operation)
```python
# events/services.py
from django.db import transaction

@transaction.atomic
def my_new_service(*, param1, param2):
    """Description of what this does"""
    # Validate
    # Create/Update/Delete
    # Return result
```

### Add a new view
```python
# events/views.py
from django.contrib.auth.decorators import login_required

@login_required
def my_new_view(request):
    """Description"""
    data = selectors.my_selector()
    return render(request, 'events/my_template.html', {'data': data})
```

### Add a new URL
```python
# events/urls.py
path('my-route/', views.my_new_view, name='my_view_name'),
```

## Testing

```bash
# Run all events tests
python manage.py test events

# Run specific test
python manage.py test events.tests.EventModelTests.test_event_slug_generation

# Check for issues
python manage.py check
```

## Debugging Tips

1. **Check logs**: Django prints helpful error messages
2. **Use Django shell**:
   ```bash
   python manage.py shell
   >>> from events.models import Event
   >>> Event.objects.all()
   ```
3. **Use admin**: http://localhost:8000/admin/ - see all data
4. **Check migrations**: `python manage.py showmigrations events`

## Git Workflow

```bash
# See current branch
git branch

# See changes
git status

# Commit changes
git add -A
git commit -m "Your message"

# Push to remote
git push origin extensive_2.2_events
```

## Important Notes

1. **Always use selectors for reads, services for writes**
2. **Keep views thin** - just parse input, call service, render template
3. **Use @transaction.atomic** for any write operation
4. **All views require @login_required**
5. **Include CSRF token in all forms**
6. **Use compact JSON format** for APIs (match existing style)
7. **Test before committing** - run `python manage.py check`

## Questions?

Refer to:
- `docs/events/PHASE1_COMPLETE.md` - Full implementation details
- `docs/events/create_event.md` - Original specification
- `docs/events/events_tab.md` - Phase 2 specification
- `docs/events/event_page.md` - Phase 3 specification

---

**Happy Coding!** 🚀

