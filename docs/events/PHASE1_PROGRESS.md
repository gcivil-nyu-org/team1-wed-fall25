# Phase 1: Events - Implementation Progress

## Completed Tasks ✅

### 1. App Foundation & Configuration
- ✅ Created `events` app with proper Django structure
- ✅ Added `EventsConfig` to `INSTALLED_APPS`
- ✅ Created directory structure:
  - `events/templates/events/`
  - `events/templates/events/partials/`
  - `events/static/events/`
- ✅ Wired events URLs to core with namespace

### 2. Database Layer - Complete Schema
- ✅ Created `events/enums.py` with all choice classes:
  - EventVisibility (PUBLIC_OPEN, PUBLIC_INVITE, PRIVATE)
  - MembershipRole (HOST, ATTENDEE, INVITED)
  - InviteStatus (PENDING, ACCEPTED, DECLINED, EXPIRED)
  - JoinRequestStatus (PENDING, APPROVED, DECLINED)

- ✅ Created all 6 models in `events/models.py`:
  - **Event** - Core event with slug auto-generation, indexes
  - **EventLocation** - Ordered stops with constraints
  - **EventMembership** - Role tracking with unique constraints
  - **EventInvite** - Invitation lifecycle tracking
  - **EventChatMessage** - Chat for Phase 3 (schema complete)
  - **EventJoinRequest** - Join requests for Phase 3 (schema complete)

- ✅ Generated and applied migrations successfully

### 3. Business Logic Layer
- ✅ Created `events/validators.py`:
  - `validate_future_datetime()` - ensures event in future
  - `validate_max_locations()` - caps at 5 locations

- ✅ Created `events/selectors.py` (read-only queries):
  - `search_locations()` - autocomplete for PublicArt
  - `search_users()` - autocomplete for users
  - `public_event_pins()` - map integration data

- ✅ Created `events/services.py` (write operations):
  - `create_event()` - atomic transaction with full business logic
    - Validates max 5 locations
    - Deduplicates locations (preserves order) and invites
    - Creates Event with auto-generated slug
    - Creates host EventMembership
    - Creates EventLocation rows
    - Creates EventInvite + EventMembership(INVITED) for invitees

### 4. Forms Layer
- ✅ Created `events/forms.py`:
  - `EventForm` with validation:
    - Title: strip + max 80 chars
    - Start time: must be future
    - Start location: must have coordinates
  - Helper functions:
    - `parse_locations()` - extracts locations[] from POST
    - `parse_invites()` - extracts invites[] from POST

### 5. Views & URLs
- ✅ Created `events/urls.py` with Phase 1 routes:
  - `/events/create/` - create event (GET/POST)
  - `/events/<slug>/` - event detail (stub)
  - `/events/api/locations/search/` - location autocomplete
  - `/events/api/users/search/` - user autocomplete
  - `/events/api/pins/` - event pins for map

- ✅ Created `events/views.py`:
  - `create()` - handles event creation with validation
  - `detail()` - stub showing event title
  - `api_locations_search()` - compact JSON format
  - `api_users_search()` - compact JSON format
  - `api_event_pins()` - map pins JSON

### 6. Templates
- ✅ Created `events/templates/events/create.html`:
  - Full form with all 8 sections
  - Title input (max 80 chars)
  - DateTime picker
  - Starting location with autocomplete
  - Description textarea
  - Additional locations (0-5 with counter)
  - Invite members with search
  - Visibility dropdown
  - Submit button

- ✅ Created `events/templates/events/detail.html`:
  - Simple stub showing event details
  - Success message

### 7. Frontend JavaScript
- ✅ Created `events/static/events/create.js`:
  - Location autocomplete with debounce
  - User autocomplete with debounce
  - Dynamic location chips (add/remove, max 5)
  - Dynamic invite chips (add/remove)
  - Location counter (n/5)
  - Form submission with hidden inputs

### 8. Admin Interface
- ✅ Created `events/admin.py`:
  - `EventAdmin` with list display, filters, search, inlines
  - `EventLocationInline` (max 5 stops)
  - `EventMembershipInline`
  - `EventChatMessageAdmin` (read-only)
  - `EventJoinRequestAdmin`

### 9. Navigation
- ✅ Updated `templates/base.html`:
  - Added "Create Event" link for authenticated users

## Implementation Details

### Database Schema
All 6 models created with proper:
- Foreign keys with `related_name`
- Indexes on frequently queried fields
- Unique constraints to prevent duplicates
- Auto-generated slugs for Event model

### Code Organization (Following Django Best Practices)
- **Enums** - Choice classes for consistency
- **Validators** - Reusable validation logic
- **Selectors** - Read-only database queries (no side effects)
- **Services** - Write operations with business logic (`@transaction.atomic`)
- **Forms** - Django ModelForm with clean methods
- **Views** - Thin controllers calling services/selectors
- **Templates** - Extending base.html, minimal inline styles
- **Static JS** - Vanilla JavaScript for autocomplete and dynamic UI

### API Endpoints (Compact JSON Format)
Following existing `loc_detail` convention:
- Locations: `{id, t, a, y, x}` (title, artist, lat, lng)
- Users: `{id, u}` (username)
- Event pins: `{id, t, y, x, slug}` (title, lat, lng, slug)

## Remaining Tasks for Phase 1

### Map Integration (Next Step)
- [ ] Update `static/js/map/` to fetch and display event pins
- [ ] Add distinct styling (purple pins for events)
- [ ] Add click handler to redirect to event detail

### Testing
- [ ] Create `events/tests.py` with:
  - Model tests (slug generation, constraints)
  - Form tests (validation rules)
  - Service tests (create_event scenarios)
  - View tests (authentication, permissions)
  - API tests (JSON responses)

### Manual Testing Checklist
- [ ] Create event with all fields
- [ ] Verify autocomplete works
- [ ] Test max 5 locations enforcement
- [ ] Verify redirect to detail page
- [ ] Check admin interface
- [ ] Verify event pin on map

## Files Created

```
events/
├── __init__.py
├── apps.py
├── models.py
├── enums.py
├── validators.py
├── selectors.py
├── services.py
├── forms.py
├── views.py
├── urls.py
├── admin.py
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py
├── templates/
│   └── events/
│       ├── create.html
│       └── detail.html
└── static/
    └── events/
        └── create.js
```

## Modified Files

- `core/settings.py` - Added EventsConfig to INSTALLED_APPS
- `core/urls.py` - Wired events URLs with namespace
- `templates/base.html` - Added Create Event link

## Database Changes

- Created 6 tables: events_event, events_eventlocation, events_eventmembership, events_eventinvite, events_eventchatmessage, events_eventjoinrequest
- Created 11 indexes for query optimization
- Created 6 unique constraints to prevent duplicates

## Next Session Notes

1. **Map Integration**: Add event pins to existing map (use purple color to distinguish from art pins)
2. **Testing**: Write comprehensive tests for models, services, and views
3. **Manual QA**: Test create event flow end-to-end
4. **Documentation**: Update user-facing docs with event creation instructions

## Commit

```
commit a5c5c62
Phase 1: Core events infrastructure - models, forms, views, and create event UI
```

