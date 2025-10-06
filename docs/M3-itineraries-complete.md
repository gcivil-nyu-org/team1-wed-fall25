# M3: Itineraries Builder Complete

## Completed Tasks

### Models
- ✅ Created Itinerary model with:
  - Owner relationship
  - Title and notes
  - is_public visibility flag
  - share_token (auto-generated via secrets)
  - Timestamps
- ✅ Created ItineraryItem model with:
  - Itinerary and location relationships
  - order_index for sequencing
  - Personal note per stop
  - Optional planned_start and planned_end times
  - Unique constraint: (itinerary, location)
- ✅ Admin registration with inline item editing

### Forms
- ✅ ItineraryForm for basic details
- ✅ ItineraryItem Form for adding stops

### Views & URLs
- ✅ itinerary_list: user's itineraries with pagination
  - Shows "Add Here" buttons when adding from location
- ✅ itinerary_detail: view with ordered stops
  - Drag-and-drop reordering via SortableJS
  - Live AJAX updates
- ✅ itinerary_create/edit: CRUD for itinerary metadata
- ✅ itinerary_delete: soft confirmation
- ✅ itinerary_item_add: add location to itinerary
  - Pre-fills location from querystring
  - Auto-assigns next order_index
- ✅ itinerary_item_reorder: AJAX endpoint for drag-drop
- ✅ itinerary_item_delete: remove stop

### Templates
- ✅ itineraries/list.html: grid of user's itineraries
- ✅ itineraries/detail.html: ordered stops with drag-drop
- ✅ itineraries/form.html: create/edit itinerary
- ✅ itineraries/item_form.html: add location

### Integration
- ✅ "Add to Itinerary" button on location detail
  - Redirects to itinerary list with location_id
  - Shows "Add Here" buttons on each itinerary
- ✅ Permission enforcement (owner-only editing)
- ✅ Drag-and-drop with SortableJS (CDN)
- ✅ AJAX reordering without page reload

## File Structure
```
itineraries/
├── admin.py (Itinerary, ItineraryItem with inline)
├── forms.py (ItineraryForm, ItineraryItemForm)
├── migrations/
│   └── 0001_initial.py
├── models.py (Itinerary, ItineraryItem)
├── urls.py (8 routes)
└── views.py (8 views)

templates/itineraries/
├── detail.html (drag-drop ordering)
├── form.html
├── item_form.html
└── list.html
```

## Database State
- Itinerary and ItineraryItem tables created
- share_token auto-generated via secrets.token_urlsafe
- Migrations applied successfully

## Next Steps (M4)
- Create Event, EventLocation, Invitation, RSVP models
- Implement event visibility (public/restricted/private)
- Invitation system with email/username
- RSVP flows

## Technical Notes
- SortableJS 1.15.0 via CDN (no npm needed)
- AJAX reordering via fetch API
- order_index managed automatically
- unique_together prevents duplicate locations per itinerary
- share_token reserved for future sharing feature
- Atomic transactions for reordering
- Permission checks on all mutations

