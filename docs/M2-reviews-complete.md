# M2: Reviews with Photos Complete

## Completed Tasks

### Models
- ✅ Created Review model with:
  - User and location relationships
  - Rating (1-5 stars with validators)
  - Text review
  - is_flagged field for moderation
  - Unique constraint: one review per user per location
  - Auto-triggers location.update_rating() on save
- ✅ Created ReviewPhoto model with:
  - Image upload (stored in review_photos/%Y/%m/)
  - Caption field
  - Order field for sorting
  - Relationship to Review
- ✅ Admin registration with inline photo editing

### Forms
- ✅ ReviewForm with radio buttons for rating
- ✅ ReviewPhotoForm for individual photos
- ✅ ReviewPhotoFormSet (up to 5 photos, 3 shown by default)

### Views & URLs
- ✅ review_create: create new review with photos
  - Checks for duplicate reviews per user
  - Atomic transaction for review + photos
- ✅ review_edit: edit review and manage photos
  - Permission check: owner or staff
  - Can add/delete photos
- ✅ review_delete: soft confirmation page
  - Permission check: owner or staff

### Templates
- ✅ reviews/form.html: unified create/edit with photo formset
- ✅ reviews/delete_confirm.html: confirmation with preview
- ✅ Updated locations/detail.html to show review photos

### Integration
- ✅ Location detail page displays reviews with photos
- ✅ Location.update_rating() recalculates average from reviews
- ✅ Review save() hook auto-updates location ratings
- ✅ Permission enforcement (owners/staff only)

## File Structure
```
reviews/
├── admin.py (Review, ReviewPhoto with inline)
├── forms.py (ReviewForm, ReviewPhotoForm, ReviewPhotoFormSet)
├── migrations/
│   └── 0001_initial.py
├── models.py (Review, ReviewPhoto)
├── urls.py (3 routes)
└── views.py (create, edit, delete)

templates/reviews/
├── delete_confirm.html
└── form.html

media/ (runtime)
└── review_photos/
    └── YYYY/MM/ (organized by upload date)
```

## Database State
- Reviews table with unique constraint on (user, location)
- ReviewPhoto table with ForeignKey to Review
- Migrations applied successfully

## Next Steps (M3)
- Create Itinerary and ItineraryItem models
- Implement CRUD for itineraries
- Add item ordering (drag/drop or up/down buttons)
- "Add to itinerary" button on location detail

## Technical Notes
- Formsets used for multiple photo uploads
- Atomic transactions for review + photos
- Denormalized rating updates via save() hook
- max_num=5 photos per review
- Photo deletion via formset DELETE checkbox
- Image storage in dated folders for organization

