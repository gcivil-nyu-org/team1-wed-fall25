# **Event Page — Detailed Task Breakdown**

*(Phase 3: Event Detail + Chat + Interaction Logic)*

---

## **1️⃣ Overview**

The **Event Page** provides two dynamic views depending on the user’s relationship to the event:

1. **Participant View (Accepted Invite)** – the user has joined or been invited and accepted.

   * Left panel → event details.
   * Right panel → event chat.

2. **Visitor View (Not yet joined)** – the user found the event via the Events tab or a public listing.

   * Left panel → event details.
   * Right panel → “Join / Apply” actions (based on visibility rules).

Both versions maintain the same visual structure for consistency.

---

## **2️⃣ UI Layout and Structure**

| Area              | Description                                 | Components                                                            |
| ----------------- | ------------------------------------------- | --------------------------------------------------------------------- |
| **Header**        | Displays event name and host.               | Event title, host avatar/name                                         |
| **Left Section**  | Shows static event data.                    | Date, Time, Itinerary, Description, Guests list                       |
| **Right Section** | Contextual area that changes by user state. | Global Chat *(for participants)* or Join/Apply panel *(for visitors)* |

---

## **3️⃣ View A — Participant (Accepted Invite)**

### **Task 1 — Event Details Panel**

#### 1.1 Layout

* [ ] Display event info:

  * Title (header)
  * Date
  * Time
  * Itinerary (linked to map route)
  * Description/message
  * Guest list (names, emails, avatars)
* [ ] Add edit option (host only).

#### 1.2 Itinerary & Navigation

* [ ] Clicking “Itinerary” opens route popup:

  * Map route of added locations (from event creation).
  * Ordered stops view.
* [ ] Reuse map module from *Art Locations* page.

---

### **Task 2 — Global Chat Panel**

#### 2.1 Chat Basics

* [ ] Display messages as chat bubbles, oldest at top.
* [ ] Refresh chat messages every **page reload** (no live updates).
* [ ] Limit to **latest 20 messages** (older ones discarded).

#### 2.2 Chat Data Model

```json
{
  "event_id": "...",
  "user_id": "...",
  "username": "...",
  "message": "...",
  "timestamp": "..."
}
```

* Store in `EventChat` table or collection.

#### 2.3 Chat API

* [ ] `GET /events/:id/chat` → returns latest 20 messages.
* [ ] `POST /events/:id/chat` → adds message.
* [ ] Auto-truncate old ones beyond limit (20).

#### 2.4 UI Components

* [ ] Chat bubble component with username + message.
* [ ] Message input box with “Send” button.
* [ ] Placeholder: “Type something…”
* [ ] Info note: “Only last 20 messages are visible.”

#### 2.5 Refresh Mechanism

* [ ] Reload chat messages on page reload or manual “Refresh Chat” button.
* [ ] Optional: auto-refresh every 60s (non-realtime).

---

## **4️⃣ View B — Visitor (Not Yet Joined)**

### **Task 3 — Event Details Panel**

* [ ] Same left-panel structure as Participant View (read-only).
* [ ] Hide guest email list until the user joins.
* [ ] Add section: *Event Visibility: Public / Invite-only*.

### **Task 4 — Join/Apply Actions**

#### 4.1 Button Logic

| Event Type           | Button Label       | Behavior                                     |
| -------------------- | ------------------ | -------------------------------------------- |
| Public + Open        | **Join Event**     | `POST /events/:id/join` → auto-add attendee. |
| Public + Invite-only | **Request Invite** | `POST /events/:id/request` → host notified.  |
| Private              | **Not accessible** | Display “Private Event — Invite Required.”   |

#### 4.2 Notifications Integration

* [ ] Change “Invitations” tab (from Chapter 2) to **“Notifications”**.
* [ ] Notifications may include:

  * Invitations received.
  * Join requests for hosted events.
* [ ] Host can Accept/Decline join requests directly from Notifications.

#### 4.3 Request Workflow

1. Visitor clicks “Request Invite”.
2. Notification sent to host:

   * Type: `"join_request"`
   * Payload: `{ requester_id, requester_name, event_id }`
3. Host action:

   * Accept → adds user to attendees list.
   * Decline → sends polite rejection notification.

#### 4.4 UI Feedback

* [ ] After clicking “Request Invite” → change label to “Requested (Pending)”.
* [ ] Disable repeat requests.

---

## **5️⃣ Task 5 — Permissions & Logic Handling**

| Role               | Permissions                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| **Host**           | Edit event details, remove guests, delete chat messages, view join requests |
| **Guest (Joined)** | View chat, send messages, view full guest list                              |
| **Visitor**        | Read-only access, can request invite or join if open                        |
| **Anonymous**      | Redirect to login page before join attempt                                  |

---

## **6️⃣ Data Models (Expanded)**

### **Event**

| Field       | Type     | Notes                                 |
| ----------- | -------- | ------------------------------------- |
| id          | string   | Unique event ID                       |
| title       | string   | Event title                           |
| description | string   | Text message                          |
| itinerary   | array    | Stops list                            |
| visibility  | enum     | PUBLIC_OPEN / PUBLIC_INVITE / PRIVATE |
| start_time  | datetime | Event time                            |
| host_id     | string   | User who created event                |

### **EventChat**

| Field      | Type     | Notes        |
| ---------- | -------- | ------------ |
| event_id   | string   | FK to Event  |
| user_id    | string   | FK to User   |
| message    | string   | Message body |
| created_at | datetime | Timestamp    |

### **Notifications**

| Field   | Type   | Notes                                 |
| ------- | ------ | ------------------------------------- |
| id      | string | Unique ID                             |
| user_id | string | Recipient                             |
| type    | enum   | INVITE / JOIN_REQUEST / STATUS_UPDATE |
| data    | json   | Custom payload                        |
| status  | enum   | UNREAD / READ                         |

---

## **7️⃣ Deliverables**

| Phase       | Deliverable                                                   | Owner      | Status |
| ----------- | ------------------------------------------------------------- | ---------- | ------ |
| UI          | Event detail + chat + join states                             | Frontend   | ☐      |
| API         | `/events/:id/chat`, `/events/:id/request`, `/events/:id/join` | Backend    | ☐      |
| DB          | Add `EventChat`, `Notifications` tables                       | Backend    | ☐      |
| Integration | Chat + Join logic to event card and notification              | Full stack | ☐      |
| Testing     | Chat refresh, join permissions, message limit                 | QA         | ☐      |

---

## **8️⃣ Django-specific Reframe — Event Page (modular plan aligned to repo)**

This section re-writes the Event Page to our Django + templates stack and the modular `events` app introduced in Create Event and Events Tab.

### A. Files and directories we will add/update

```
events/
  urls.py                 # add detail/chat/request routes
  views.py                # detail, chat_send, chat_latest?, request_invite
  selectors.py            # get_event, user_role, list_attendees, list_chat_messages
  services.py             # post_chat_message, request_invite
  models.py               # add EventChatMessage (+ optional EventJoinRequest)
  templates/
    events/
      detail.html
      partials/
        _details_panel.html
        _chat_panel.html
        _cta_panel.html
  static/events/
    detail.js             # optional progressive enhancement (poll chat)
```

All business reads go through `selectors`; all writes go through `services`. Views are thin.

### B. URL patterns (namespace `events`)

- `path('<slug:slug>/', views.detail, name='detail')`
- `path('<slug:slug>/chat/send/', views.chat_send, name='chat_send')` (POST)
- `path('<slug:slug>/chat/latest/', views.chat_latest, name='chat_latest')` (GET JSON, optional)
- `path('<slug:slug>/request/', views.request_invite, name='request_invite')` (POST; invite-only)

Note: Join/Accept/Decline already covered in Events Tab plan.

### C. Views (contracts)

- `detail(request, slug)`
  - `@login_required`
  - Fetch event via `selectors.get_event(slug)` with `select_related('host','start_location')` and `prefetch_related('locations','memberships__user')`.
  - Determine `user_role = selectors.user_role(event, request.user)` → `'HOST' | 'ATTENDEE' | 'VISITOR'`.
  - If participant, fetch `chat_messages = selectors.list_chat_messages(event, limit=20)`.
  - Build context: `event, user_role, attendees, additional_locations, chat_messages?` and render `events/detail.html`.

- `chat_send(request, slug)`
  - `@login_required`, `@require_POST`.
  - Validate user is HOST/ATTENDEE; on fail → 403 with message.
  - `services.post_chat_message(event, request.user, request.POST['message'])`.
  - Redirect back to `events:detail` (anchor `#chat`).

- `chat_latest(request, slug)` (optional)
  - `@login_required`, returns JSON `{messages:[{u, m, t}]}` where `u=username`, `m=message`, `t=ISO timestamp}` from `selectors.list_chat_messages`.

- `request_invite(request, slug)`
  - `@login_required`, `@require_POST`.
  - Only allowed when event.visibility == `PUBLIC_INVITE` and user not already attendee or invited.
  - Call `services.request_invite(event, request.user)`; flash “Request sent”. Redirect back.

### D. Templates (context and partials)

- `detail.html` receives: `event, user_role, attendees, additional_locations, chat_messages?`.
  - Renders header with event title and host.
  - Includes `partials/_details_panel.html` (left) and either `partials/_chat_panel.html` or `partials/_cta_panel.html` (right) based on `user_role`.

- `_details_panel.html`
  - Shows Date (formatted), Time, Start location (link to `loc_detail:art_detail`), Description, Attendees list (names; emails only for HOST).
  - Shows ordered additional locations; “View on Map” link (post-MVP) can reuse existing compact points style.

- `_chat_panel.html`
  - Loops over `chat_messages` oldest→newest.
  - Form with textarea `name="message"`, CSRF, action `events:chat_send`.
  - Text: “Only the latest 20 messages are shown.”

- `_cta_panel.html`
  - If `visibility == PUBLIC_OPEN` → Join button posting to `events:join`.
  - If `visibility == PUBLIC_INVITE` → Request Invite button posting to `events:request_invite` (disabled after submit).
  - If `visibility == PRIVATE` → notice only.

### E. Selectors (read-only)

- `get_event(slug)` → event with related fields for the page.
- `user_role(event, user)` → `'HOST' | 'ATTENDEE' | 'VISITOR'`.
- `list_attendees(event)` → users with `EventMembership.role in {HOST, ATTENDEE}`.
- `list_chat_messages(event, limit=20)` → latest 20 ordered ascending.

### F. Services (mutations)

- `post_chat_message(event, user, message)`
  - Validates membership, trims whitespace, requires 1..300 chars.
  - Creates `EventChatMessage` then enforces per-event retention by deleting oldest beyond 20.

- `request_invite(event, user)`
  - Idempotent: if membership/invite exists → no-op.
  - Creates `EventJoinRequest(status=PENDING)`; later can notify host.

### G. Models (additions in `events/models.py`)

- `EventChatMessage(event, author, message, created_at)` with index on `(event, -created_at)`.
- `EventJoinRequest(event, requester, status, created_at, decided_at?)` with `UniqueConstraint(event, requester)`.

### H. Permissions summary

- HOST: can view details, chat, later moderate.
- ATTENDEE: can view details and chat.
- VISITOR: read-only; may Join (Public-Open) or Request Invite (Public-Invite).
- All views require login; anonymous users are redirected by Django.

### I. Request/Response contracts

- `POST /events/<slug>/chat/send/` form fields: `message` → redirect back to detail with toast.
- `GET  /events/<slug>/chat/latest/` response: `{messages:[{u, m, t}]}` (optional enhancement).
- `POST /events/<slug>/request/` → sends/records request; redirect back with disabled button state on the client.

### J. Testing checklist

- Selector coverage: `get_event`, role derivation, chat retrieval ordering.
- Service coverage: chat validation + retention; request idempotency and visibility rules.
- View tests: permissions per role, CSRF on posts, redirects.
- Template smoke tests: conditional panels render correctly for each role.

### K. Implementation order (recommended)

1) Models + migrations (EventChatMessage, optional EventJoinRequest).
2) Selectors (`get_event`, `user_role`, `list_chat_messages`).
3) Views: `detail` rendering with placeholders, then `chat_send`.
4) Templates and partials; wire CSRF and messages.
5) Add `request_invite` flow (optional for MVP if Events Tab already covers invites).
6) Optional `chat_latest` + `static/events/detail.js` polling.

### L. Integration notes

- Reuse visibility and role enums from `events/enums.py` created in Create Event plan.
- Reuse join endpoint and invite handling from Events Tab; Event Page CTA simply posts to those URLs.
- Map integration for itinerary uses the compact points convention already used by `loc_detail.api_all_points` (post-MVP).