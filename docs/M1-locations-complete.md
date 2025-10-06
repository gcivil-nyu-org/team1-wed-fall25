# M1: Locations & Map Complete

## Completed Tasks

### Models
- ✅ Created Tag model (name, slug, category)
- ✅ Created Location model with:
  - Basic info (name, description)
  - Full address fields
  - Geolocation (lat/lng with indexes)
  - Media (website_url, image_url)
  - Source tracking (seeded vs user-contributed, source_id)
  - Denormalized ratings (average_rating, review_count)
  - M2M relationship with Tags
- ✅ Created Favorite model (user-location unique constraint)
- ✅ Admin registration for all models

### Views & URLs
- ✅ location_list: filterable/searchable list with map
  - Search by name/description/address
  - Filter by tag
  - Filter by map bounding box (viewport)
  - Sort by rating, review count, newest, name
  - Pagination (20 per page)
- ✅ location_detail: full details with reviews preview
- ✅ location_create: authenticated users can add locations
- ✅ location_edit: owners/staff can edit
- ✅ location_favorite_toggle: AJAX-ready favorite/unfavorite
- ✅ favorites_list: user's favorited locations

### Templates
- ✅ locations/list.html: map + filters + cards
- ✅ locations/detail.html: single location with embedded map
- ✅ locations/form.html: create/edit with interactive map
- ✅ locations/favorites.html: favorites grid

### Forms
- ✅ LocationForm with map coordinate pickers
- ✅ Validation for lat/lng ranges

### Seeding
- ✅ Management command: `load_nyc_art`
  - Supports CSV and JSON formats
  - Upsert by source_id (idempotent)
  - Dry-run mode
  - Sample data: 10 NYC public art locations loaded
  - Auto-tags with "Public Art"

### Map Integration
- ✅ Leaflet maps on all location pages
- ✅ Dynamic markers from locations data
- ✅ Click-to-place on create/edit forms
- ✅ Draggable markers
- ✅ User geolocation on homepage

## File Structure
```
locations/
├── admin.py (Tag, Location, Favorite)
├── forms.py (LocationForm)
├── management/
│   └── commands/
│       └── load_nyc_art.py (seeding command)
├── migrations/
│   └── 0001_initial.py
├── models.py (Tag, Location, Favorite)
├── urls.py (7 routes)
└── views.py (6 views)

templates/locations/
├── detail.html
├── favorites.html
├── form.html
└── list.html

data/
└── sample_nyc_art.csv (10 locations)
```

## Database State
- 10 locations seeded
- 1 tag created ("Public Art")
- Ready for user contributions

## Next Steps (M2)
- Create Review and ReviewPhoto models
- Implement review CRUD
- Link reviews to locations
- Photo uploads
- Update location.update_rating() hook

## Technical Notes
- Decimal fields for precise geolocation
- Composite indexes on (latitude, longitude) and (source, source_id)
- Denormalized rating fields for performance
- AJAX-ready favorite toggle (JSON response on XHR)
- Permission checks: owners/staff can edit locations

