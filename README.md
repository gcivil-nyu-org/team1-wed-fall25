# Artinerary - NYC Public Art Discovery Platform

Artinerary is a Django web application that helps users discover, plan, and share visits to outdoor public art in New York City. Built with Django templates, Leaflet maps, and PostgreSQL.

## Features

### Core Functionality
- **Interactive Map**: Browse NYC public art locations on an OpenStreetMap-powered Leaflet map
- **Location Management**: Search, filter, and discover art venues with ratings and reviews
- **Reviews with Photos**: Write detailed reviews with up to 5 photos per review
- **Favorites**: Save your favorite locations for quick access
- **Itineraries**: Build custom art tours with drag-and-drop ordering
- **Events**: Create public or private art events with RSVP functionality
- **Invitations**: Invite users by username or email to restricted events
- **Reporting**: Flag inappropriate content for moderation

### User Roles
- **Art Explorers**: Discover locations, write reviews, create itineraries
- **Event Organizers**: Host public or private art tours and meetups
- **Administrators**: Seed venue data, moderate reports, manage content

## Tech Stack

- **Backend**: Django 5.2.7, Python 3.13
- **Database**: PostgreSQL (via psycopg)
- **Frontend**: Django Templates, vanilla JavaScript, Leaflet 1.9.4
- **Styling**: CSS (no frameworks - lightweight and fast)
- **Media**: Pillow for image handling
- **Maps**: Leaflet + OpenStreetMap (no API keys required)

## Project Structure

```
Project/
├── accounts/          # User authentication and profiles
├── locations/         # Art venues, tags, favorites
├── reviews/           # Reviews with photo uploads
├── itineraries/       # Personal itinerary builder
├── events/            # Events, invitations, RSVPs
├── reports/           # Content moderation system
├── core/              # Settings, base URLs, homepage
├── templates/         # Django templates
│   ├── base.html
│   ├── home.html
│   ├── accounts/
│   ├── locations/
│   ├── reviews/
│   ├── itineraries/
│   ├── events/
│   └── reports/
├── static/
│   ├── css/site.css
│   └── js/map.js
├── media/             # User uploads (avatars, review photos)
├── data/              # Seed data (sample_nyc_art.csv)
└── docs/              # Milestone documentation

```

## Installation & Setup

### Prerequisites
- Python 3.13+
- PostgreSQL 12+
- Git

### Steps

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd Project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\Activate.ps1
   # Mac/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp env.template .env
   # Edit .env with your settings:
   # - SECRET_KEY
   # - DEBUG (True for dev)
   # - DB_NAME, DB_USER, DB_PASSWORD
   ```

5. **Setup PostgreSQL database**
   ```bash
   createdb artinerary_db
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Load sample data (optional)**
   ```bash
   python manage.py load_nyc_art data/sample_nyc_art.csv
   ```

9. **Run development server**
   ```bash
   python manage.py runserver
   ```

10. **Access the site**
    - Homepage: http://127.0.0.1:8000/
    - Admin: http://127.0.0.1:8000/admin/

## Management Commands

### Load NYC Open Data
```bash
# CSV format
python manage.py load_nyc_art path/to/file.csv

# JSON format
python manage.py load_nyc_art path/to/file.json --format json

# Dry run (preview without saving)
python manage.py load_nyc_art path/to/file.csv --dry-run
```

Expected CSV columns: `name`, `description`, `address`, `latitude`, `longitude`, `id`

## Key Features Guide

### 1. Locations
- Browse on interactive map
- Search by name/description/address
- Filter by tags and bounding box
- Sort by rating, review count, newest
- Add new locations (authenticated users)

### 2. Reviews
- Rate locations 1-5 stars
- Upload up to 5 photos per review
- One review per user per location
- Auto-updates location ratings

### 3. Itineraries
- Create personal art tours
- Add locations from detail pages
- Drag-and-drop to reorder stops
- Optional timing for each stop
- Public or private visibility

### 4. Events
- **Public**: Anyone can view and RSVP
- **Restricted**: Invitation-only
- **Private**: Owner-only
- Link to itineraries for multi-stop events
- RSVP status: Going, Maybe, Not Going
- Capacity limits (optional)

### 5. Invitations
- Invite by username or email
- Token-based acceptance
- Email notifications (console backend in dev)
- 7-day expiration

### 6. Reporting
- Report locations, reviews, events
- Generic system for all content types
- Admin moderation interface
- Status tracking (open → resolved)

## Database Models

### Core Models
- **User** (Django built-in)
- **UserProfile**: Extended profile (avatar, bio, home location)
- **Tag**: Categories for locations
- **Location**: Art venues with geolocation
- **Favorite**: User favorites
- **Review**: Ratings and text reviews
- **ReviewPhoto**: Photo attachments
- **Itinerary**: User-created routes
- **ItineraryItem**: Locations in itineraries
- **Event**: Art events
- **EventLocation**: Locations in events
- **Invitation**: Event invites
- **RSVP**: Event attendance status
- **Report**: Content moderation

## Admin Features

Access Django admin at `/admin/` with superuser credentials:

- **Seed Data**: Use admin or management command
- **Moderate Reports**: Review flagged content
- **Manage Users**: View profiles, activity
- **Content Management**: Edit/delete any content
- **Bulk Operations**: Django admin actions

## Development Notes

### Django Templates (No React)
- Server-side rendering for all pages
- Minimal JavaScript for interactivity (map, drag-drop)
- Progressive enhancement approach
- No build pipeline required

### Map Integration
- Leaflet 1.9.4 via CDN
- OpenStreetMap tiles (free, no API key)
- User geolocation for "nearby" features
- Click-to-place markers on forms

### File Uploads
- Avatars: `media/avatars/`
- Review photos: `media/review_photos/YYYY/MM/`
- Django media URL handling in dev
- Serve via nginx/S3 in production

### Email
- Console backend in development
- Set `EMAIL_BACKEND` for production (SMTP/SendGrid)

## Testing

```bash
# Run all tests
python manage.py test

# Run specific app
python manage.py test locations

# With coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## Deployment Considerations

### Static Files
```bash
python manage.py collectstatic
```

### Environment Variables (Production)
- `DEBUG=False`
- `SECRET_KEY` (unique, secure)
- `ALLOWED_HOSTS` (your domain)
- `DATABASE_URL` or RDS credentials
- `EMAIL_BACKEND` (SMTP settings)
- `MEDIA_ROOT` and `STATIC_ROOT`

### Security
- HTTPS required
- CSRF protection enabled
- SQL injection protected (Django ORM)
- XSS protection (template auto-escaping)
- Login required for mutations

### Performance
- Database indexes on lat/lng, created_at, source_id
- Denormalized ratings for fast queries
- Pagination (20 items per page)
- Select/prefetch related for N+1 prevention

## Documentation

See `docs/` folder for milestone completion reports:
- `M0-foundations-complete.md`
- `M1-locations-complete.md`
- `M2-reviews-complete.md`
- `M3-itineraries-complete.md`
- `M4-events-complete.md`
- `M5-reports-complete.md`

## Contributing

This is a university project. For issues or questions, contact the development team.

## License

Educational project - see course policies.

## Team

- Product Owner: Hashmmath
- Development Team: Chrissy, David, Nived, Hashmmath
- University: NYU
- Course: Software Engineering

---

**Built with Django 5.2.7 | Lean Code, Clean Code**
