# **Events Tab — Detailed Task Breakdown**

*(Phase 2: Event Discovery & Invitation Management UI)*

---

## **1️⃣ Overview**

The **Events Tab** acts as the central hub for exploring, managing, and creating events within the app.
It includes **three functional sections** represented as tabs or buttons:

1. **Public Events** – browse and join open or invite-based public events.
2. **Invitations** – manage event invites with Accept/Decline actions.
3. **Create Event** – launch the event creation workflow (from Chapter 1).

The layout design prioritizes clarity and quick navigation, following the sketch provided.

---

## **2️⃣ UI Layout and Flow**

| Section                   | Description                                                           | Components                                                                                  |
| ------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **Header Bar**            | Fixed top bar displaying tab buttons and “Create Event” action.       | - Tabs: *Public Events*, *Invitations*<br>- Floating “+ Create Event” button on right       |
| **Public Events Section** | Displays all discoverable events marked as *public*.                  | - Event cards (grid/list view)<br>- Search/filter bar<br>- Join button per event            |
| **Invitations Section**   | Displays events that have invited the logged-in user.                 | - Invitation cards<br>- Accept / Decline buttons<br>- Auto-redirect to event page on accept |
| **Create Event Button**   | Opens “Create Event” workflow modal or navigates to `/events/create`. | - Floating “+” icon<br>- Tooltip: “Create a new event”                                      |

---

## **3️⃣ Implementation Tasks & Subtasks**

### **Task 1 — Navigation & Layout (Django templates)**

#### 1.1 URL patterns (namespace: `events`)

* [ ] In `events/urls.py`:

  - `path("", views.index, name="index")` → landing wrapper that defaults to Public tab
  - `path("public/", views.public_events, name="public")`
  - `path("invitations/", views.invitations, name="invitations")`
  - `path("create/", views.create, name="create")` (from Create Event plan)
  - Action endpoints (POST):
    - `path("<slug:slug>/join/", views.join_event, name="join")`
    - `path("<slug:slug>/accept/", views.accept_invite, name="accept")`
    - `path("<slug:slug>/decline/", views.decline_invite, name="decline")`

* [ ] Wire include in `core/urls.py`: `path("events/", include(("events.urls", "events"), namespace="events"))`

#### 1.2 Tabs bar (Header) and templates

* [ ] Base template: `templates/events/base_tabs.html` with a nav bar:
  - Tabs: `events:public`, `events:invitations` and a right-aligned button to `events:create`
  - Active tab highlighted using request.path matching
* [ ] Views `public_events` and `invitations` extend `base_tabs.html` and render their list sections.
* [ ] Responsive layout with stacked nav for mobile.

---

### **Task 2 — Public Events Section (server-rendered + thin JS)**

#### 2.1 Selector and service contracts

* [ ] In `events/selectors.py`:
  - `list_public_events(query: str | None, visibility_filter: str | None, order: str | None) -> QuerySet[Event]`
    - Filters: visibility in `{PUBLIC_OPEN, PUBLIC_INVITE}`; search across title, host.username, start_location.title
    - Ordering: default by `start_time` ascending; supports `-start_time`
  - `user_has_joined(event, user) -> bool`

* [ ] In `events/services.py`:
  - `join_event(*, event: Event, user: User) -> None` with business rules:
    - Public Open: anyone can join
    - Public Invite: require existing invite or host role
    - Private: reject
    - Upsert `EventMembership(user, role=ATTENDEE)`

#### 2.2 View and template

* [ ] `views.public_events(request)`
  - `@login_required` parses `q`, `filter` in `{open, invite}`, `sort` in `{date, -date}`
  - Uses `selectors.list_public_events(...)`
  - Annotate `.joined` flag using membership existence for `request.user`
  - Pagination via `Paginator` (e.g., 12 per page)
  - Renders `templates/events/public_events.html`

* [ ] Template `public_events.html` shows cards with:
  - Title, host username, formatted datetime, start location title
  - Visibility pill (Open/Invite)
  - `Join` button posts to `events:join` with `{slug}` (disabled if already joined)
  - `View` links to `events:detail` (from Create Event plan)

#### 2.3 POST endpoint for joining

* [ ] `views.join_event(request, slug)`
  - `@login_required`, `@require_POST`, fetch event by slug, call `services.join_event`
  - On success: message + redirect back to `events:public` with current query params

#### 2.4 Empty state

* [ ] If queryset empty, render helper card: “No public events yet. Be the first to create one!” + link to `events:create`.

---

### **Task 3 — Invitations Section (server-rendered + POST actions)**

#### 3.1 Selector and service contracts

* [ ] In `events/selectors.py`:
  - `list_user_invitations(user: User) -> QuerySet[EventInvite]` with select_related(`event`, `event.host`, `event.start_location`)

* [ ] In `events/services.py`:
  - `accept_invite(*, invite: EventInvite) -> None` → set `status=ACCEPTED`, upsert `EventMembership(role=ATTENDEE)`
  - `decline_invite(*, invite: EventInvite) -> None` → set `status=DECLINED`

#### 3.2 View and template

* [ ] `views.invitations(request)`
  - `@login_required`, fetch pending invites via `selectors.list_user_invitations`
  - Renders `templates/events/invitations.html`

* [ ] Template shows invitation cards with: event fields + two small forms/buttons posting to `events:accept` / `events:decline`.

#### 3.3 POST action endpoints

* [ ] `views.accept_invite(request, slug)`
  - Validate invite exists for `request.user` and event `slug`
  - Call `services.accept_invite`
  - Redirect to `events:detail`

* [ ] `views.decline_invite(request, slug)`
  - Validate invite exists and call `services.decline_invite`
  - Redirect back to `events:invitations`

#### 3.4 Empty state

* [ ] Render “No pending invitations.” with subtle help text linking to Public tab.

---

### **Task 4 — Create Event Button**

#### 4.1 Button behavior

* [ ] Right-aligned button in `base_tabs.html` linking to `{% url 'events:create' %}` with a `+` icon.

#### 4.2 Permissions

* [ ] The `create` view is `@login_required`; unauthenticated users will be redirected to login per Django settings.

---

### **Task 5 — State Management**

* [ ] Tabs are route-driven (`/events/public/`, `/events/invitations/`).
* [ ] Use Django pagination; keep `q`, `filter`, `sort`, and `page` as query params and preserve them on actions.
* [ ] Optional progressive enhancement: small JS snippet to keep scroll position and toasts.

---

## **4️⃣ Data Flow Summary (Django endpoints)**

| User Action             | Endpoint (method)                         | Result                                        |
| ----------------------- | ----------------------------------------- | --------------------------------------------- |
| Opens “Public Events”   | `GET /events/public/`                     | Render list with pagination and filters       |
| Joins a public event    | `POST /events/<slug>/join/`               | Adds membership; flash message                |
| Opens “Invitations”     | `GET /events/invitations/`                | Render pending invitations                    |
| Accepts invitation      | `POST /events/<slug>/accept/`             | Creates attendee membership; redirect detail  |
| Declines invitation     | `POST /events/<slug>/decline/`            | Marks declined; stays on invitations          |
| Clicks “+ Create Event” | `GET /events/create/`                     | Opens event creation flow                     |

---

## **5️⃣ Deliverables**

| Phase       | Deliverable                                       | Owner      | Status |
| ----------- | ------------------------------------------------- | ---------- | ------ |
| UI          | Tabs base + `public_events.html` + `invitations.html` | Frontend   | ☐      |
| Backend     | Selectors + services + views + URL wiring         | Backend    | ☐      |
| Actions     | Join/Accept/Decline POST endpoints                | Full stack | ☐      |
| Integration | Link to Create flow + messages/toasts             | Full stack | ☐      |
| Testing     | Unit tests for services and selector logic        | QA         | ☐      |

---

## **6️⃣ Backend modules and contracts (modularity guide)**

- `selectors.py` is read-only and safe for caching. No side effects.
- `services.py` performs mutations inside `transaction.atomic()` and raises domain exceptions like `JoinNotAllowed`, `InviteNotFound` used by views for user feedback.
- Views are thin: parse inputs → call selector/service → pick template or redirect.
- Templates contain no business logic; reusable partials `_event_card.html`, `_invite_card.html` live under `templates/events/partials/`.
- Keep all constants in `enums.py` to share between forms, services, and admin.


---