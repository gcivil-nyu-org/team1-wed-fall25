# Frontend Template: Artinerary Homepage

## Overview
This document describes the homepage template (`templates/artinerary/home.html`) that displays an interactive map of NYC public art locations.

## File Location
```
templates/artinerary/home.html
```

## Template Structure

### Base Template
Extends `base.html` for consistent site layout:
```django
{% extends "base.html" %}
{% load static %}
```

### Page Title
```django
{% block title %}Artinerary - NYC Public Art Map{% endblock %}
```

## Dependencies (CDN)

### Leaflet Core
```html
<!-- CSS -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
     integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
     crossorigin=""/>

<!-- JS -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
     integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
     crossorigin=""></script>
```

### Leaflet MarkerCluster Plugin
```html
<!-- CSS -->
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />

<!-- JS -->
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
```

## Styling

### Map Container
```css
#map {
    height: calc(100vh - 120px);  /* Full viewport minus header/footer */
    width: 100%;
    margin-top: 20px;
}

.map-container {
    padding: 0;  /* Full-width map */
}
```

### Popup Styles
```css
.leaflet-popup-content {
    margin: 10px;
    min-width: 200px;
}

.popup-title {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 5px;
    color: #333;
}

.popup-artist {
    font-size: 14px;
    color: #666;
    margin-bottom: 5px;
}

.popup-borough {
    font-size: 12px;
    color: #999;
    margin-bottom: 10px;
}
```

### Action Buttons
```css
.popup-actions {
    display: flex;
    gap: 10px;
    align-items: center;
    margin-top: 10px;
}

.btn-view-details {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 8px 16px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 14px;
    cursor: pointer;
    border-radius: 4px;
}

.btn-view-details:hover {
    background-color: #45a049;
}
```

### Favorite Heart Icon
```css
.favorite-heart {
    font-size: 24px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.favorite-heart.not-favorited {
    color: #ddd;  /* Gray when not favorited */
}

.favorite-heart.favorited {
    color: #e74c3c;  /* Red when favorited */
}

.favorite-heart:hover {
    transform: scale(1.2);
}
```

## HTML Content

### Main Content Block
```html
{% block content %}
<div class="container-fluid map-container">
    <h1 class="text-center">NYC Public Art Map</h1>
    <p class="text-center text-muted">Explore public art installations across New York City</p>
    <div id="map"></div>
</div>
{% endblock %}
```

### JavaScript Integration
```html
{% block extra_js %}
<script src="{% static 'js/home_map.js' %}"></script>
{% endblock %}
```

## View Integration

**File**: `artinerary/views.py`
```python
@login_required
def index(request):
    """Artinerary homepage with interactive map"""
    return render(request, 'artinerary/home.html')
```

**URL**: `/artinerary/`

## User Flow
1. User navigates to `/artinerary/`
2. Must be logged in (redirected to login if not)
3. Page loads with full-screen map
4. JavaScript (`home_map.js`) initializes and fetches art locations
5. Map displays clustered markers
6. User can:
   - Zoom/pan the map
   - Click clusters to expand
   - Click individual markers to see popup
   - Click "View Details" to go to detail page
   - Click heart icon to add/remove from favorites

## Responsive Design
- Map takes full viewport height minus header/footer
- Container uses `container-fluid` for full-width layout
- Mobile-friendly with Leaflet's touch support

## Performance Considerations
- Uses CDN-hosted libraries (cached by browser)
- Lazy loads map data via AJAX after page render
- MarkerCluster reduces DOM elements with many markers
- Custom JS loaded last to ensure dependencies are available

## Related Files
- `artinerary/views.py` - View handler
- `artinerary/urls.py` - URL routing
- `static/js/home_map.js` - Map initialization and interaction
- `base.html` - Base template with navigation
- `loc_detail/views.py` - API endpoints for data

## Testing Checklist
- [ ] Map renders correctly on desktop
- [ ] Map renders correctly on mobile
- [ ] Clusters form and expand properly
- [ ] Popups display all information
- [ ] "View Details" button navigates correctly
- [ ] Heart icon toggles favorite status
- [ ] Authentication required to access page

