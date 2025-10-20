# Event Creation Feature — Detailed Task Breakdown

*(Phase 1 of 3: "Create Event" Page Implementation for Artinerary)*

---

## **1️⃣ Overview — Phase 1 in Context**

**Phase 1 (THIS DOC):** Create Event page + backend foundation  
**Phase 2:** Events Tab (browse, join, manage invitations) — see `events_tab.md`  
**Phase 3:** Event Detail Page (chat, visitor actions) — see `event_page.md`

The "Create Event" flow enables a logged-in user to author a new event with:
- Title, date/time, starting location (required)
- Optional: additional locations (up to 5), description, invited members
- Visibility mode: PUBLIC_OPEN, PUBLIC_INVITE, or PRIVATE

When published, the event:
* Appears in the *Events Tab* (Phase 2) if public
* Shows as a **pinpoint on the map** at the starting location
* Redirects to the *Event Detail Page* (Phase 3)

**Critical:** This phase establishes the database schema, services, and selectors that Phases 2 and 3 will consume. All models must be complete now.

---

## **2️⃣ UI Structure & Components**

| Section                                | Purpose                                      | Type / Interaction                                |
| -------------------------------------- | -------------------------------------------- | ------------------------------------------------- |
| **1. Title**                           | Name of event                                | Text input                                        |
| **2. Date & Time**                     | Event schedule                               | Date & time picker                                |
| **3. Starting Location**               | Mandatory base pin for event                 | Search existing location *or* select on map       |
| **4. Description**                     | Brief details                                | Multi-line text field                             |
| **5. Additional Locations (optional)** | Add up to 5 art locations as itinerary stops | Trello-style “+ Add Card” component               |
| **6. Invite Members**                  | Add usernames to send invites                | Trello-style “+ Add Card” component + user search |
| **7. Visibility Mode**                 | Choose Public / Private                      | Dropdown + conditional buttons (Open / Invite)    |
| **8. Submit**                          | Save + publish event                         | “Create Event” button with validation             |

---

## **3️⃣ Implementation Tasks & Sub-tasks**

### **Task 1 — Frontend UI (Django Templates + Vanilla JS)**

**Note:** We use Django templates (HTML/CSS/JS), NOT React or FlutterFlow per professor's guidance.

#### 1.1 Page Layout (`templates/events/create.html`)

* [ ] Create route `GET /events/create` → `events:create` view.
* [ ] Extend `templates/base.html` (site-wide base with nav).
* [ ] Scrollable form container with CSRF token.
* [ ] Form action: `POST /events/create`.
* [ ] Define sections in visual order (see §2).

#### 1.2 Title Field

* [ ] Text input with max length (80 chars).
* [ ] Add real-time validation (non-empty).

#### 1.3 Date Picker

* [ ] Integrate native date + time pickers.
* [ ] Store ISO string in state.
* [ ] Add “date must be future” validation.

#### 1.4 Starting Location Selector

* [ ] Two interaction modes (tabs or toggle): **Search Existing Locations** / **Pick on Map**.
* [ ] For "Search": AJAX call to `GET /events/api/locations/search?q=<term>` (defined in §2.3).
  - Display autocomplete results with title, artist, borough.
  - On select: populate hidden input `start_location` with PublicArt ID.
* [ ] For "Pick on Map" (post-MVP): open map modal reusing `static/js/map/` modules; user clicks pin → capture lat/lng and search nearest PublicArt or allow creating temp location.
* [ ] Display selected location card showing title and artist.
* [ ] Hidden input: `<input name="start_location" value="{{ selected_id }}">`.

#### 1.5 Description Field

* [ ] Multi-line TextArea (300 chars max).
* [ ] Optional field.

#### 1.6 Additional Locations Section (0–5)

* [ ] Reusable card component similar to Trello Add Card.
* [ ] “+ Add Location” → opens search modal → select → append to list.
* [ ] Reorder via drag / up-down buttons.
* [ ] Remove button per location.
* [ ] Display counter `n/5`.

#### 1.7 Invite Members Section

* [ ] Reuse card component logic from 1.6.
* [ ] "+ Add Member" → AJAX call to `GET /events/api/users/search?q=<term>` (defined in §2.3).
  - Autocomplete with username (email optional).
  - On select: append user chip to UI and add hidden input `<input name="invites[]" value="{{ user_id }}">`.
* [ ] Display selected user with username (avatar optional for Phase 1).
* [ ] Remove button per user → deletes corresponding hidden input.
* [ ] JS captures array of user IDs from all `invites[]` inputs on submit.

#### 1.8 Visibility Mode Dropdown

* [ ] Dropdown with “Public” / “Private”.
* [ ] If “Public”: show radio buttons (Open / Invite).
* [ ] If “Private”: hide extra options.
* [ ] Store enum in state (`PUBLIC_OPEN`, `PUBLIC_INVITE`, `PRIVATE`).

#### 1.9 Submit Button

* [ ] Validate required fields (title, date, start location).
* [ ] Disable until valid.
* [ ] On submit, call `POST /events` with body (see Task 3).
* [ ] On success → redirect to Event Page (`/events/:id`).

---

### **Task 2 — Backend (Django, modular and template-first)**

This reframes the backend to match our Django repo and template-based UI. We will build a self-contained `events` app with clean boundaries and small, composable modules. All endpoints are server-rendered views or lightweight JSON APIs consumed by vanilla JS in templates.

#### 2.0 App layout (files we will create in `events/`)

```
events/
  apps.py
  models.py
  enums.py                  # visibility, membership roles, invite status
  validators.py             # reusable field and cross-field validators
  selectors.py              # read-only query helpers
  services.py               # write actions (create_event, add_invites, ...)
  forms.py                  # EventForm + thin helper forms
  urls.py
  views.py                  # HTML views + JSON APIs
  admin.py
  templates/
    events/
      create.html           # matches Task 1 layout
      _location_card.html   # partial
      _user_chip.html       # partial
  static/events/            # scoped JS for this page only
    create.js               # search + add/remove + submit
```

Notes:
- Keep querying logic in `selectors.py` and mutations in `services.py` so future features (edit, delete, share links, chat) compose over the same primitives.
- The UI remains Django templates; JSON endpoints return minimal payloads for autocomplete and are consumed by `static/events/create.js`.

#### 2.1 Database models (in `events/models.py`) — COMPLETE FOR ALL 3 PHASES

**Phase 1 models (create now):**

- **Event** (core entity)
  - Fields:
    - `id` (AutoField, PK)
    - `slug` (SlugField, unique, indexed, auto-generated from title+uuid snippet)
    - `title` (CharField, max_length=80)
    - `host` (FK → `auth.User`, on_delete=CASCADE, related_name='hosted_events')
    - `visibility` (CharField, choices from `enums.EventVisibility`: `PUBLIC_OPEN`, `PUBLIC_INVITE`, `PRIVATE`)
    - `start_time` (DateTimeField, indexed)
    - `start_location` (FK → `loc_detail.PublicArt`, on_delete=PROTECT, related_name='events')
    - `description` (TextField, blank=True, max 300 chars enforced in form)
    - `is_deleted` (BooleanField, default=False, for soft deletes)
    - `created_at` (DateTimeField, auto_now_add=True)
    - `updated_at` (DateTimeField, auto_now=True)
  - Constraints:
    - `UniqueConstraint(fields=['host', TruncDate('start_time'), 'title'], name='uniq_host_title_per_day')`
  - Indexes: `slug`, `start_time`, `visibility`, `(host, start_time)`
  - Methods:
    - `get_absolute_url()` → `reverse('events:detail', kwargs={'slug': self.slug})`
    - `save()` override to auto-generate slug if empty

- **EventLocation** (ordered itinerary stops; 0-5 additional locations beyond start)
  - Fields:
    - `event` (FK → `Event`, on_delete=CASCADE, related_name='locations')
    - `location` (FK → `loc_detail.PublicArt`, on_delete=PROTECT)
    - `order` (PositiveSmallIntegerField, 1..5)
    - `note` (CharField, max_length=100, blank=True)
  - Constraints:
    - `UniqueConstraint(fields=['event', 'order'], name='uniq_event_location_order')`
    - `UniqueConstraint(fields=['event', 'location'], name='uniq_event_location_pair')`
  - Ordering: `['order']`

- **EventMembership** (who is in the event and their role)
  - Fields:
    - `event` (FK → `Event`, on_delete=CASCADE, related_name='memberships')
    - `user` (FK → `auth.User`, on_delete=CASCADE, related_name='event_memberships')
    - `role` (CharField, choices from `enums.MembershipRole`: `HOST`, `ATTENDEE`, `INVITED`)
    - `joined_at` (DateTimeField, auto_now_add=True)
  - Constraints:
    - `UniqueConstraint(fields=['event', 'user'], name='uniq_event_user_membership')`
  - Indexes: `(event, role)`, `user`
  - Note: `INVITED` role is set when invite created; changes to `ATTENDEE` when accepted (Phase 2)

- **EventInvite** (tracks invite lifecycle)
  - Fields:
    - `event` (FK → `Event`, on_delete=CASCADE, related_name='invites')
    - `invited_by` (FK → `auth.User`, on_delete=SET_NULL, null=True)
    - `invitee` (FK → `auth.User`, on_delete=CASCADE, related_name='event_invitations')
    - `status` (CharField, choices from `enums.InviteStatus`: `PENDING`, `ACCEPTED`, `DECLINED`, `EXPIRED`)
    - `created_at` (DateTimeField, auto_now_add=True)
    - `responded_at` (DateTimeField, null=True, blank=True)
  - Constraints:
    - `UniqueConstraint(fields=['event', 'invitee'], name='uniq_event_invitee')`
  - Indexes: `(invitee, status)`, `event`

**Phase 3 models (add in Phase 1 migration for schema completeness):**

- **EventChatMessage** (chat for attendees/host)
  - Fields:
    - `event` (FK → `Event`, on_delete=CASCADE, related_name='chat_messages')
    - `author` (FK → `auth.User`, on_delete=CASCADE)
    - `message` (CharField, max_length=300)
    - `created_at` (DateTimeField, auto_now_add=True, indexed)
  - Indexes: `(event, -created_at)` for retrieval
  - Retention: service enforces max 20 messages per event

- **EventJoinRequest** (for PUBLIC_INVITE events; visitors request to join)
  - Fields:
    - `event` (FK → `Event`, on_delete=CASCADE, related_name='join_requests')
    - `requester` (FK → `auth.User`, on_delete=CASCADE)
    - `status` (CharField, choices: `PENDING`, `APPROVED`, `DECLINED`)
    - `created_at` (DateTimeField, auto_now_add=True)
    - `decided_at` (DateTimeField, null=True, blank=True)
  - Constraints:
    - `UniqueConstraint(fields=['event', 'requester'], name='uniq_event_join_request')`
  - Indexes: `(event, status)`, `requester`

**Admin registration (`events/admin.py`):**
- `EventAdmin` with `list_display=['title', 'host', 'start_time', 'visibility', 'created_at']`, filters on `visibility`, `start_time`, `host`.
  - Inlines: `EventLocationInline` (tabular, max 5), `EventMembershipInline` (tabular).
- `EventChatMessageAdmin` (read-only, list by event).
- `EventJoinRequestAdmin` with actions to approve/decline.

**Migration strategy:**
1. Create initial migration with all 6 models (ensures schema ready for all phases).
2. Add constraints and indexes in same or follow-up migration.
3. Populate `enums.py` before migrating.

#### 2.2 URLs (in `events/urls.py` and wired under `core/urls.py` with namespace `events`) — ALL PHASES

**Wire in `core/urls.py`:**
```python
urlpatterns = [
    ...
    path('events/', include(('events.urls', 'events'), namespace='events')),
]
```

**Phase 1 URLs (`events/urls.py`):**
```python
from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # CREATE
    path('create/', views.create, name='create'),  # GET/POST
    
    # DETAIL (stub for Phase 1, full in Phase 3)
    path('<slug:slug>/', views.detail, name='detail'),
    
    # HELPER APIs (autocomplete for create form)
    path('api/locations/search/', views.api_locations_search, name='api_locations_search'),
    path('api/users/search/', views.api_users_search, name='api_users_search'),
    path('api/pins/', views.api_event_pins, name='api_event_pins'),  # for map integration
]
```

**Phase 2 URLs (add to same file):**
```python
    # BROWSE & MANAGE
    path('', views.index, name='index'),  # redirect to public by default
    path('public/', views.public_events, name='public'),
    path('invitations/', views.invitations, name='invitations'),
    
    # ACTIONS
    path('<slug:slug>/join/', views.join_event, name='join'),
    path('<slug:slug>/accept/', views.accept_invite, name='accept'),
    path('<slug:slug>/decline/', views.decline_invite, name='decline'),
```

**Phase 3 URLs (add to same file):**
```python
    # CHAT & VISITOR ACTIONS
    path('<slug:slug>/chat/send/', views.chat_send, name='chat_send'),
    path('<slug:slug>/chat/latest/', views.chat_latest, name='chat_latest'),  # optional
    path('<slug:slug>/request/', views.request_invite, name='request_invite'),
```

**Rationale:** All event routes under `/events/` namespace; helper APIs stay scoped to this app while reusing `loc_detail.PublicArt` and `auth.User`.

#### 2.3 Views & JSON APIs (in `events/views.py`)

- `create(request)`
  - `@login_required` GET: render `EventForm` and inject small config (URLs, max limits) to the template.
  - POST: validate `EventForm` + parse `locations[]` and `invites[]` from request (flat arrays), then call `services.create_event(...)` inside `transaction.atomic()`.
  - On success: `messages.success` and `redirect(event.get_absolute_url())`.

- `detail(request, slug)`
  - Simple view for now; shows event summary. Acts as post-create target.

- `api_locations_search(request)`
  - `@login_required`, returns compact list from `selectors.search_locations(term, limit=10)`.
  - Reuse `loc_detail.PublicArt` with fields: `{id, title, artist_name, latitude, longitude}`; output compact keys `{id, t, a, y, x}` to match existing map docs style.

- `api_users_search(request)`
  - `@login_required`, `q` against `auth.User.username__icontains` or `email__icontains`.
  - Output: `{id, u, a}` where `u= username`, `a= avatar_url (placeholder for now)}`.

- `api_event_pins(request)`
  - Returns `{"points": [{"id": event.id, "t": event.title, "y": lat, "x": lng}]}` for public events only; later we can scope by visibility/attendee.

All JSON endpoints use `JsonResponse`, are GET-only, and capped (e.g., 10 results) to keep them snappy.

#### 2.4 Forms (in `events/forms.py`)

- `EventForm(ModelForm)` with fields: `title`, `start_time`, `start_location`, `visibility`, `description`.
  - `clean_start_time`: must be future.
  - `clean_title`: strip + length ≤ 80.
  - `clean`: cross-field validation (e.g., ensure start_location exists and coordinates present).
- Lightweight helpers for arrays handled in JS:
  - `parse_locations(request)` → returns ordered list of up to 5 `PublicArt` ids.
  - `parse_invites(request)` → returns distinct list of user ids, excluding self.

Why not formsets? We keep the UX Trello-style and post arrays; the server still enforces constraints and creates rows in a transaction.

#### 2.5 Services (in `events/services.py`)

- `create_event(*, host: User, form: EventForm, locations: list[int], invites: list[int]) -> Event`
  - Validates business rules not covered by the form:
    - max 5 locations; dedupe while preserving order
    - forbid duplicate title on same date for same host
    - ensure all location ids exist
    - ensure all invitee ids exist and are not the host
  - Creates `Event`, `EventMembership(role=HOST)`, `EventLocation` rows in order, and `EventInvite` rows with `PENDING` status.
  - Emits `event_created` signal (see below).

Keep service pure and reusable so `Edit Event` can reuse it later.

#### 2.6 Selectors (in `events/selectors.py`)

- `search_locations(term: str, limit=10)` → queryset over `PublicArt` (title/artist/location icontains, with non-null lat/lng) returning only fields needed.
- `search_users(term: str, limit=10)` → queryset over `auth.User`.
- `public_event_pins()` → values needed by the map layer.

#### 2.7 Validators (in `events/validators.py`)

- `validate_future_datetime(value)`
- `validate_visibility(value)` (choices)
- Composite validator used by service: `validate_max_locations(locations, max_allowed=5)`.

#### 2.8 Signals (modular integration)

- `event_created` Django signal dispatched from `services.create_event` with payload `{event_id}`.
- Receiver in `events/signals.py` can later push to caches or websockets; for now it’s a no-op placeholder to keep extensibility.

#### 2.9 Admin (in `events/admin.py`)

- `EventAdmin` with `list_display = (title, host, start_time, visibility)` and inlines for `EventLocation` and `EventMembership`.

#### 2.10 Security & permissions

- All endpoints require `@login_required`.
- JSON endpoints additionally enforce throttling via simple rate limiting (future) and return minimal fields.
- `api_event_pins` exposes only public events for now.

#### 2.11 Request/Response contracts

- Create submit (form POST to `/events/create`):

  Body fields (form-encoded):
  - `title: str`
  - `start_time: ISO8601 string from `<input type="datetime-local">``
  - `start_location: int` (PublicArt id)
  - `description: str?`
  - `visibility: PUBLIC_OPEN | PUBLIC_INVITE | PRIVATE`
  - `locations[]: int` (0..5, ordered)
  - `invites[]: int` (0..N, deduped server-side)

  Response: redirect to `events:detail` on success; otherwise re-render with errors.

- `GET /events/api/locations/search?q=<term>` →
  ```json
  { "results": [ { "id": 1, "t": "Title", "a": "Artist", "y": 40.7, "x": -73.9 } ] }
  ```

- `GET /events/api/users/search?q=<term>` →
  ```json
  { "results": [ { "id": 4, "u": "alice" } ] }
  ```

- `GET /events/api/pins` →
  ```json
  { "points": [ { "id": 12, "t": "Gallery Crawl", "y": 40.7, "x": -73.9 } ] }
  ```

These match our existing compact style used by `loc_detail.api_all_points` for easy map integration.


---

---

## **5️⃣ Ultra-Granular Setup & Implementation Order (ALL 3 PHASES)**

### **Step 0: Prerequisites (before Phase 1)**

* [ ] Ensure `loc_detail` app exists with `PublicArt` model and is migrated.
* [ ] Ensure `accounts` app exists with Django's `auth.User` (or custom User model).
* [ ] Confirm `templates/base.html` exists (site-wide base template).
* [ ] Confirm `static/css/site.css` and `static/js/` directories exist.

### **Step 1: Create `events` app structure**

```bash
# In project root
python manage.py startapp events
```

* [ ] Add `'events'` to `INSTALLED_APPS` in `core/settings.py`.
* [ ] Create subdirectories:
  ```
  mkdir events/templates/events
  mkdir events/templates/events/partials
  mkdir events/static/events
  ```

### **Step 2: Define enums (`events/enums.py`)**

```python
from django.db import models

class EventVisibility(models.TextChoices):
    PUBLIC_OPEN = 'PUBLIC_OPEN', 'Public - Open to All'
    PUBLIC_INVITE = 'PUBLIC_INVITE', 'Public - Invite Only'
    PRIVATE = 'PRIVATE', 'Private'

class MembershipRole(models.TextChoices):
    HOST = 'HOST', 'Host'
    ATTENDEE = 'ATTENDEE', 'Attendee'
    INVITED = 'INVITED', 'Invited'

class InviteStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    ACCEPTED = 'ACCEPTED', 'Accepted'
    DECLINED = 'DECLINED', 'Declined'
    EXPIRED = 'EXPIRED', 'Expired'

class JoinRequestStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    DECLINED = 'DECLINED', 'Declined'
```

### **Step 3: Create models (`events/models.py`)**

* [ ] Import `PublicArt` from `loc_detail.models`.
* [ ] Import enums from `events.enums`.
* [ ] Define all 6 models as per §2.1 (Event, EventLocation, EventMembership, EventInvite, EventChatMessage, EventJoinRequest).
* [ ] Add `__str__` methods for each model.
* [ ] Override `Event.save()` to auto-generate slug using `slugify(title)` + short UUID.

### **Step 4: Create and run migrations**

```bash
python manage.py makemigrations events
python manage.py migrate events
```

* [ ] Verify all constraints and indexes in migration file.
* [ ] Test migration rollback/forward for safety.

### **Step 5: Register models in admin (`events/admin.py`)**

```python
from django.contrib import admin
from .models import Event, EventLocation, EventMembership, EventInvite, EventChatMessage, EventJoinRequest

class EventLocationInline(admin.TabularInline):
    model = EventLocation
    extra = 1
    max_num = 5

class EventMembershipInline(admin.TabularInline):
    model = EventMembership
    extra = 0

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'host', 'start_time', 'visibility', 'created_at']
    list_filter = ['visibility', 'start_time', 'created_at']
    search_fields = ['title', 'host__username']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    inlines = [EventLocationInline, EventMembershipInline]

@admin.register(EventChatMessage)
class EventChatMessageAdmin(admin.ModelAdmin):
    list_display = ['event', 'author', 'message', 'created_at']
    list_filter = ['event', 'created_at']
    readonly_fields = ['created_at']

@admin.register(EventJoinRequest)
class EventJoinRequestAdmin(admin.ModelAdmin):
    list_display = ['event', 'requester', 'status', 'created_at']
    list_filter = ['status', 'event']
    actions = ['approve_requests', 'decline_requests']
```

### **Step 6: Create validators (`events/validators.py`)**

```python
from django.core.exceptions import ValidationError
from django.utils import timezone

def validate_future_datetime(value):
    if value <= timezone.now():
        raise ValidationError('Event must be in the future.')

def validate_max_locations(locations, max_allowed=5):
    if len(locations) > max_allowed:
        raise ValidationError(f'Maximum {max_allowed} locations allowed.')
```

### **Step 7: Create selectors (`events/selectors.py`) — PHASE 1**

```python
from django.db.models import Q
from loc_detail.models import PublicArt
from django.contrib.auth import get_user_model

User = get_user_model()

def search_locations(term: str, limit=10):
    return PublicArt.objects.filter(
        Q(title__icontains=term) | Q(artist_name__icontains=term) | Q(location__icontains=term),
        latitude__isnull=False,
        longitude__isnull=False
    ).values('id', 'title', 'artist_name', 'latitude', 'longitude')[:limit]

def search_users(term: str, limit=10):
    return User.objects.filter(
        Q(username__icontains=term) | Q(email__icontains=term)
    ).values('id', 'username')[:limit]

def public_event_pins():
    from .models import Event
    from .enums import EventVisibility
    return Event.objects.filter(
        visibility__in=[EventVisibility.PUBLIC_OPEN, EventVisibility.PUBLIC_INVITE],
        is_deleted=False
    ).select_related('start_location').values(
        'id', 'slug', 'title', 
        'start_location__latitude', 
        'start_location__longitude'
    )
```

### **Step 8: Create services (`events/services.py`) — PHASE 1**

```python
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Event, EventLocation, EventMembership, EventInvite
from .enums import MembershipRole, InviteStatus
from .validators import validate_max_locations
from loc_detail.models import PublicArt

User = get_user_model()

@transaction.atomic
def create_event(*, host: User, form, locations: list[int], invites: list[int]):
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
        raise ValueError('One or more locations are invalid.')
    
    # Dedupe invites and exclude host
    unique_invites = list(set(invites) - {host.id})
    
    # Ensure all invitee IDs exist
    valid_users = User.objects.filter(id__in=unique_invites)
    if valid_users.count() != len(unique_invites):
        raise ValueError('One or more invitees are invalid.')
    
    # Create event
    event = form.save(commit=False)
    event.host = host
    event.save()
    
    # Create host membership
    EventMembership.objects.create(event=event, user=host, role=MembershipRole.HOST)
    
    # Create location stops
    for order, loc_id in enumerate(unique_locations, start=1):
        EventLocation.objects.create(
            event=event,
            location_id=loc_id,
            order=order
        )
    
    # Create invites
    for invitee_id in unique_invites:
        EventInvite.objects.create(
            event=event,
            invited_by=host,
            invitee_id=invitee_id,
            status=InviteStatus.PENDING
        )
        # Also create membership with INVITED role
        EventMembership.objects.create(
            event=event,
            user_id=invitee_id,
            role=MembershipRole.INVITED
        )
    
    return event
```

### **Step 9: Create forms (`events/forms.py`) — PHASE 1**

```python
from django import forms
from .models import Event
from .validators import validate_future_datetime
from loc_detail.models import PublicArt

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'start_time', 'start_location', 'visibility', 'description']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4, 'maxlength': 300}),
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) > 80:
            raise forms.ValidationError('Title must be 80 characters or less.')
        return title
    
    def clean_start_time(self):
        start_time = self.cleaned_data.get('start_time')
        validate_future_datetime(start_time)
        return start_time
    
    def clean_start_location(self):
        location = self.cleaned_data.get('start_location')
        if not location.latitude or not location.longitude:
            raise forms.ValidationError('Selected location must have valid coordinates.')
        return location

def parse_locations(request):
    """Parse locations[] from POST data."""
    locations = request.POST.getlist('locations[]')
    return [int(loc_id) for loc_id in locations if loc_id.isdigit()]

def parse_invites(request):
    """Parse invites[] from POST data."""
    invites = request.POST.getlist('invites[]')
    return [int(user_id) for user_id in invites if user_id.isdigit()]
```

### **Step 10: Create views (`events/views.py`) — PHASE 1**

* [ ] Implement `create(request)` (GET/POST).
* [ ] Implement stub `detail(request, slug)` (just shows event title for now; Phase 3 completes it).
* [ ] Implement JSON APIs: `api_locations_search`, `api_users_search`, `api_event_pins`.
* [ ] All views use `@login_required`.

### **Step 11: Wire URLs (`events/urls.py` and `core/urls.py`)**

* [ ] Create `events/urls.py` with Phase 1 routes (see §2.2).
* [ ] Add `path('events/', include(...))` to `core/urls.py`.

### **Step 12: Create templates — PHASE 1**

* [ ] `templates/events/create.html` (full form with all sections from §2).
* [ ] `templates/events/partials/_location_card.html` (reusable for location chips).
* [ ] `templates/events/partials/_user_chip.html` (reusable for invite chips).
* [ ] Stub `templates/events/detail.html` (just title + "Event created successfully" for Phase 1).

### **Step 13: Create static JS (`static/events/create.js`)**

* [ ] Autocomplete for locations using `fetch('/events/api/locations/search?q=...')`.
* [ ] Autocomplete for users using `fetch('/events/api/users/search?q=...')`.
* [ ] Dynamic add/remove for location and invite chips.
* [ ] Form validation before submit.

### **Step 14: Test Phase 1**

* [ ] Create event via form.
* [ ] Verify event in admin.
* [ ] Verify redirect to detail page.
* [ ] Test autocomplete APIs.

---

### **Phase 2 & 3 Implementation (see respective docs)**

* Phase 2: Add `public_events`, `invitations`, `join_event`, `accept_invite`, `decline_invite` views and templates (see `events_tab.md`).
* Phase 3: Add `detail` (full), `chat_send`, `chat_latest`, `request_invite` views, chat panel, CTA panel (see `event_page.md`).

---

## **6️⃣ Deliverables — Phase 1 Checklist**

| Component                  | File(s)                                          | Status |
| -------------------------- | ------------------------------------------------ | ------ |
| **Enums**                  | `events/enums.py`                                | ☐      |
| **Models (all 6)**         | `events/models.py`                               | ☐      |
| **Migrations**             | `events/migrations/0001_initial.py`              | ☐      |
| **Admin**                  | `events/admin.py`                                | ☐      |
| **Validators**             | `events/validators.py`                           | ☐      |
| **Selectors (Phase 1)**    | `events/selectors.py`                            | ☐      |
| **Services (Phase 1)**     | `events/services.py`                             | ☐      |
| **Forms**                  | `events/forms.py`                                | ☐      |
| **Views (create + APIs)**  | `events/views.py`                                | ☐      |
| **URLs (Phase 1)**         | `events/urls.py` + wire in `core/urls.py`        | ☐      |
| **Templates**              | `create.html`, `detail.html` (stub), partials    | ☐      |
| **Static JS**              | `static/events/create.js`                        | ☐      |
| **Map Integration**        | Update `static/js/map/` to consume event pins    | ☐      |
| **Unit Tests**             | `events/tests.py` (forms, services, validators)  | ☐      |
| **Integration Tests**      | Test create flow end-to-end                      | ☐      |

---

## **7️⃣ Cross-Phase Integration & Future Work**

### **Phase 1 → Phase 2 handoff:**
- Phase 2 will consume:
  - `Event`, `EventMembership`, `EventInvite` models (already created)
  - `selectors.list_public_events()`, `selectors.list_user_invitations()` (add in Phase 2)
  - `services.join_event()`, `services.accept_invite()`, `services.decline_invite()` (add in Phase 2)
- Phase 1 must ensure all models and enums are complete; Phase 2 only adds views/templates.

### **Phase 2 → Phase 3 handoff:**
- Phase 3 will consume:
  - `EventChatMessage`, `EventJoinRequest` models (already created in Phase 1)
  - `selectors.get_event()`, `selectors.user_role()`, `selectors.list_chat_messages()` (add in Phase 3)
  - `services.post_chat_message()`, `services.request_invite()` (add in Phase 3)
- Phase 3 completes the `detail` view and adds chat/visitor panels.

### **Map integration notes:**
- Phase 1: Add event pins to map using `api_event_pins` endpoint.
- Reuse `static/js/map/layers.js` and `markers.js` pattern.
- Event pins use distinct color/icon (e.g., purple) vs art pins (current).
- Click event pin → `window.location.href = '/events/' + event.slug`.

### **Testing strategy across phases:**
1. **Phase 1:** Unit test models, services, forms; integration test create flow.
2. **Phase 2:** Test join/accept/decline workflows; test public/private visibility logic.
3. **Phase 3:** Test chat retention (20 msg limit); test role-based panel rendering.

### **Future enhancements (post-MVP):**
- Edit/delete events (reuse `create_event` service with update logic).
- Shareable event links (generate token, allow anonymous access to public events).
- Real-time chat (WebSocket layer over `EventChatMessage`).
- Notifications system (email/push for invites, join requests).
- Event search and filters (date range, location proximity).

---
