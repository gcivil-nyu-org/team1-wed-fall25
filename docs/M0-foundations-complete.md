# M0: Foundations Complete

## Completed Tasks

### 0.1-0.2: Settings & Requirements
- ✅ Added Pillow==11.0.0 to requirements.txt
- ✅ Configured INSTALLED_APPS: accounts, locations, reviews, itineraries, events, reports
- ✅ Set up STATIC_ROOT and MEDIA_ROOT for file uploads
- ✅ Configured LOGIN_REDIRECT_URL='/', LOGIN_URL, email backend (console)

### 0.3: Base Template
- ✅ Enhanced templates/base.html with full navigation
- ✅ Added nav links: Map, Locations, Itineraries, Events, Favorites, Profile
- ✅ Flash messages support
- ✅ Blocks: title, extra_head, content, extra_js

### 0.4: Homepage & Core URLs
- ✅ Created core/views.py with homepage view
- ✅ Created templates/home.html with Leaflet map integration
- ✅ Set up core/urls.py routing all app URLs
- ✅ Added media URL handling for development
- ✅ Created URL stubs for all apps: locations, reviews, itineraries, events, reports
- ✅ Created placeholder views for all apps (prevent 500 errors)

### Map Integration
- ✅ Created static/js/map.js with Leaflet initialization
- ✅ Map centered on NYC (40.7128, -74.0060)
- ✅ User location detection with geolocation API
- ✅ Dynamic marker loading from window.locationsData

### 1.1-1.6: Accounts & Profile
- ✅ Created UserProfile model (display_name, bio, avatar, home_lat, home_lng)
- ✅ Auto-create profile on user signup via signals
- ✅ Created UserProfileForm combining User and Profile fields
- ✅ Implemented profile_view and profile_edit views
- ✅ Created templates: accounts/profile.html, accounts/profile_edit.html
- ✅ Registered UserProfile in admin
- ✅ Ran migrations successfully

## File Structure
```
Project/
├── accounts/
│   ├── admin.py (UserProfile registered)
│   ├── forms.py (SignupForm, EmailOrUsernameAuthenticationForm, UserProfileForm)
│   ├── models.py (UserProfile with signals)
│   ├── urls.py (signup, login, logout, profile, profile_edit)
│   └── views.py (SignupView, CustomLoginView, logout_view, profile_view, profile_edit)
├── core/
│   ├── settings.py (all apps configured, media setup)
│   ├── urls.py (all app routes)
│   └── views.py (homepage)
├── locations/ (stub views & URLs)
├── reviews/ (stub views & URLs)
├── itineraries/ (stub views & URLs)
├── events/ (stub views & URLs)
├── reports/ (stub views & URLs)
├── static/
│   ├── css/site.css
│   └── js/map.js (Leaflet integration)
└── templates/
    ├── base.html (enhanced nav)
    ├── home.html (map homepage)
    └── accounts/
        ├── login.html
        ├── signup.html
        ├── profile.html
        └── profile_edit.html
```

## Next Steps (M1)
- Create Location and Tag models
- Build locations list/detail views with Leaflet map
- Implement favorites toggle
- NYC Open Data seeding command

## Technical Notes
- Django 5.2.7, PostgreSQL via psycopg
- Leaflet 1.9.4 via CDN (no API keys needed)
- Image uploads via Pillow
- Console email backend for development

