# Gap Analysis: Current Branch vs Epics and Project Details

## Executive Summary
- Current branch centers on a login-gated public art browser implemented in `loc_detail` with NYC Open Data ingestion, list/search/filter by borough, detail page, and user comments.
- Accounts provide signup/login/logout with email-or-username.
- Many epics (ratings/photos reviews, favorites UX, itineraries, events, reporting, embedded maps) are not yet implemented here.
- Admin ingestion from NYC Open Data is implemented and robust enough for MVP seeding.

## System Snapshot (as-built)
- Apps
  - `accounts`: signup, login (email/username), logout.
  - `loc_detail`: ingest NYC public art, browse/search/paginate, art detail, comments.
  - `artinerary`: placeholder hello.
  - `events`, `itineraries`, `locations`, `reports`, `reviews`: present as skeleton/migrations only; not active.
- Routing
  - `core/urls.py`: `/accounts/`, `/artinerary/`, `/loc_detail/`, `/admin/`.
  - `loc_detail/urls.py`: `""` (list), `"art/<int:art_id>/"` (detail).
- Auth
  - Login required for `/loc_detail/` list and detail; login redirects to `/loc_detail/`.
- Data Ingestion
  - `loc_detail.management.commands.import_art_data`: pulls CSV from NYC Open Data `2pg3-gcaa`, cleans values, validates lat/lng, upserts `PublicArt` via `external_id`.
- Data Models (active)
  - `PublicArt`: artist, title, description, location, borough, latitude/longitude, medium, years, agency, community_board, `external_id`, timestamps.
  - `ArtComment`: user, art, comment, timestamps.
  - `UserFavoriteArt`: user, art, notes, added_at, unique(user, art). No user-facing UI yet.
- Templates/UI
  - `templates/base.html`: nav (Browse Art, auth links), flash messages.
  - `templates/loc_detail/art_list.html`: search, borough filter, cards, pagination.
  - `templates/loc_detail/art_detail.html`: metadata, Google Maps outbound link (if coords), comments, related items.
- Admin
  - `loc_detail.admin`: searchable/filterable `PublicArt`; `ArtComment`; `UserFavoriteArt` admin.

## Epics Mapping: DONE vs REMAINING

### 1) Registration and Account Management
- DONE
  - Signup with email + username; login with email-or-username; logout; redirect to `/loc_detail/`.
- REMAINING
  - Password reset flow; account deletion; user profile (view/edit, avatar); password change; optional email verification.

### 2) Manage & Review Art Locations
- DONE
  - Seed/browse `PublicArt`; search title/artist/description/location; filter by borough; paginate; detailed view; text comments; admin tooling.
- PARTIAL
  - Favorites: model exists, no toggle/list UI or endpoints.
- REMAINING
  - Reviews with star ratings (1–5) and photos; rating aggregation on items; user-submitted locations; embedded map with markers; nearby/viewport filters; favorites UX.

### 3) Build & Manage Itineraries
- DONE
  - None.
- REMAINING
  - `Itinerary` + `ItineraryItem` models; CRUD; reorder UX; add-from-detail; visibility; save/unsave.

### 4) Create, Manage & Share Events
- DONE
  - None.
- REMAINING
  - `Event`, `EventLocation`, `Invitation`, `RSVP` models; CRUD; visibility (public/restricted/private); invites by username/email; token acceptance; RSVP; capacity; event lists.

### 5) Chat Functionality (Post-MVP)
- DONE
  - None.
- REMAINING
  - Group chat for events; moderation; P2P chat (post-MVP by plan).

### 6) Reporting Content
- DONE
  - None.
- REMAINING
  - Report model (generic FK); report submission flows for location/review/user/event; admin moderation UI (status, severity, notes); notifications.

### 7) Administrator
- DONE
  - NYC Open Data seed via management command; admin CRUD.
- REMAINING
  - Review user reports; account/content flagging; moderation workflows; policy enforcement.

## Project Details (MVP) vs Current
- Map with nearby places: REMAINING (no embedded map; only external Google Maps link on detail).
- Add a place on map: REMAINING (no user location creation flow; seeded only).
- Add reviews (text, image): REMAINING (only comments; no ratings/photos).
- Events (single/multi-stop): REMAINING (no events feature in-branch).
- 2.1 User Profile/Account Creation: PARTIAL (signup/login); REMAINING (password reset; profile management).
- 2.2 Event visibility: REMAINING.

## Current Data Flows (Implemented)
- Ingestion: NYC Open Data → CSV → clean/normalize → validate coords → update_or_create `PublicArt` by `external_id`.
- Browse: `/loc_detail/` (auth required) → search/borough filters → paginate 20/page → list template.
- Detail: `/loc_detail/art/<id>/` (auth required) → details + related items → comment form.
- Commenting: POST to detail → create `ArtComment` → redirect with message.
- Admin: manage PublicArt, ArtComment, UserFavoriteArt.

## Cross-Cutting Gaps
- Auth scope: list/detail are behind login; epics imply public discovery. Confirm intended access model.
- Geospatial UX: no embedded map/markers; no “nearby” or viewport filtering.
- Media: no user-facing image uploads yet (reviews/photos).
- Profiles: no extended `UserProfile` entity.
- Reporting/moderation: no end-user flows; admin-only deletion available.

## Risks
- External dataset schema changes; network/API availability.
- Low discovery without ratings/reviews and public visibility.
- No embedded maps reduces UX parity with MVP goals.

## Summary
- Strong foundation for data ingestion and authenticated browsing/comments of NYC public art.
- Major user-facing epics (reviews with photos, favorites UX, maps, itineraries, events, reporting) remain to be implemented on this branch to meet MVP/MLP.
