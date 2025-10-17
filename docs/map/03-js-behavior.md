# Frontend JavaScript: Map Behavior

## Overview
This document describes the JavaScript implementation (`static/js/home_map.js`) that powers the interactive map on the Artinerary homepage.

## File Location
```
static/js/home_map.js
```

## Architecture

### IIFE Pattern
Uses Immediately Invoked Function Expression to avoid global namespace pollution:
```javascript
(function() {
    'use strict';
    // All code encapsulated here
})();
```

## Core Components

### 1. Map Initialization with Geolocation
```javascript
const map = L.map('map');
map.locate({ setView: true, maxZoom: 14, enableHighAccuracy: true });
```
- Initializes map without fixed view
- Requests user's current location via browser Geolocation API
- If allowed: centers on user location at zoom 14
- If denied: falls back to NYC coordinates (40.7128°N, 74.0060°W) at zoom 11

### 2. User Location Detection

**Location Found Handler:**
```javascript
map.on('locationfound', function(e) {
    const radius = e.accuracy / 2;
    
    // Blue dot marker (Google Maps style)
    const userIcon = L.divIcon({
        className: 'user-location-marker',
        html: '<div class="user-dot"></div>',
        iconSize: [20, 20]
    });
    
    userMarker = L.marker(e.latlng, { icon: userIcon }).addTo(map)
        .bindPopup("You are here (±" + Math.round(radius) + " meters)")
        .openPopup();
    
    L.circle(e.latlng, radius, {
        color: '#4285F4',
        fillColor: '#4285F4',
        fillOpacity: 0.1,
        weight: 1
    }).addTo(map);
});
```
- Creates animated blue dot marker at user location
- Adds accuracy circle showing location precision
- Opens popup showing accuracy radius

**Location Error Handler:**
```javascript
map.on('locationerror', function(e) {
    console.log('Location access denied or unavailable:', e.message);
    map.setView([40.7128, -74.0060], 11);
    
    // Show friendly message
    const notice = document.getElementById('location-notice');
    const noticeText = document.getElementById('notice-text');
    if (notice && noticeText) {
        noticeText.textContent = 'Location access not available. Showing NYC area instead.';
        notice.style.display = 'block';
        setTimeout(() => notice.style.display = 'none', 5000);
    }
});
```
- Falls back to NYC center view
- Displays temporary message to user
- Auto-hides message after 5 seconds

### 3. Tile Layer (OpenStreetMap)
```javascript
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
}).addTo(map);
```
- Uses OpenStreetMap tiles (free, no API key required)
- Max zoom: 19 (street level)
- Proper attribution included

### 4. Marker Clustering
```javascript
const markers = L.markerClusterGroup({
    maxClusterRadius: 50,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true
});
```

**Configuration**:
- `maxClusterRadius: 50` - Markers within 50px cluster together
- `spiderfyOnMaxZoom: true` - Spreads markers at max zoom
- `showCoverageOnHover: false` - Cleaner UI, no hover polygons
- `zoomToBoundsOnClick: true` - Clicking cluster zooms to show all its markers

## Helper Functions

### CSRF Token Retrieval
```javascript
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');
```
- Required for POST requests to Django backend
- Extracted from cookies

### Toggle Favorite
```javascript
function toggleFavorite(artId, heartElement) {
    fetch(`/loc_detail/api/favorite/${artId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.favorited) {
            heartElement.classList.remove('not-favorited');
            heartElement.classList.add('favorited');
            alert('Location added to favourites');
        } else {
            heartElement.classList.remove('favorited');
            heartElement.classList.add('not-favorited');
            alert('Location removed from favourites');
        }
    })
    .catch(error => {
        console.error('Error toggling favorite:', error);
        alert('Failed to update favorites. Please try again.');
    });
}
```

**Behavior**:
- Makes POST request to toggle endpoint
- Updates heart icon styling based on response
- Shows user feedback via alert
- Handles errors gracefully

### Create Popup Content
```javascript
function createPopupContent(point) {
    const popupDiv = document.createElement('div');
    
    // Title
    const title = document.createElement('div');
    title.className = 'popup-title';
    title.textContent = point.t;
    popupDiv.appendChild(title);
    
    // Artist
    const artist = document.createElement('div');
    artist.className = 'popup-artist';
    artist.textContent = `by ${point.a}`;
    popupDiv.appendChild(artist);
    
    // Borough (optional)
    if (point.b) {
        const borough = document.createElement('div');
        borough.className = 'popup-borough';
        borough.textContent = point.b;
        popupDiv.appendChild(borough);
    }
    
    // Actions container
    const actions = document.createElement('div');
    actions.className = 'popup-actions';
    
    // View Details button
    const detailBtn = document.createElement('a');
    detailBtn.href = `/loc_detail/art/${point.id}/`;
    detailBtn.className = 'btn-view-details';
    detailBtn.textContent = 'View Details';
    actions.appendChild(detailBtn);
    
    // Heart icon for favorites
    const heart = document.createElement('span');
    heart.className = 'favorite-heart not-favorited';
    heart.innerHTML = '&#10084;';
    heart.title = 'Add to favorites';
    heart.onclick = function(e) {
        e.preventDefault();
        toggleFavorite(point.id, heart);
    };
    actions.appendChild(heart);
    
    popupDiv.appendChild(actions);
    
    return popupDiv;
}
```

**Features**:
- Dynamically builds popup HTML from point data
- Uses DOM methods for safe HTML creation
- Conditionally shows borough if available
- Attaches click handler to heart icon
- Returns DOM element (not HTML string)

## Data Loading

### Fetch All Points
```javascript
fetch('/loc_detail/api/points/all')
    .then(response => response.json())
    .then(data => {
        console.log(`Loaded ${data.points.length} art locations`);
        
        data.points.forEach(point => {
            const marker = L.marker([point.y, point.x]);
            const popupContent = createPopupContent(point);
            marker.bindPopup(popupContent);
            markers.addLayer(marker);
        });
        
        // Add marker cluster to map
        map.addLayer(markers);
        
        // Fit bounds to show all markers
        if (data.points.length > 0) {
            map.fitBounds(markers.getBounds(), { padding: [50, 50] });
        }
    })
    .catch(error => {
        console.error('Error loading art locations:', error);
        alert('Failed to load art locations. Please refresh the page.');
    });
```

**Process**:
1. Fetch all points from backend API
2. Log count for debugging
3. Create marker for each point
4. Bind popup with custom content
5. Add marker to cluster group
6. Add cluster group to map
7. Auto-fit map bounds to show all markers
8. Handle errors with user-friendly message

## Data Flow

```
Page Load
  ↓
home_map.js executes
  ↓
Initialize Leaflet map
  ↓
Fetch /loc_detail/api/points/all
  ↓
Receive JSON: {points: [{id, t, a, b, y, x}, ...]}
  ↓
Create marker for each point
  ↓
Build popup with:
  - Title, artist, borough
  - "View Details" link
  - Heart icon (favorite toggle)
  ↓
Add all markers to cluster group
  ↓
Add cluster group to map
  ↓
Fit map to show all markers
```

## User Interactions

### 1. Click Cluster
- Zooms in to show individual markers
- Handled by Leaflet MarkerCluster plugin

### 2. Click Marker
- Opens popup with art information
- Popup stays open until closed or another marker clicked

### 3. Click "View Details"
- Navigates to `/loc_detail/art/<id>/`
- Full page navigation (not AJAX)

### 4. Click Heart Icon
- Prevents popup from closing (`e.preventDefault()`)
- Makes POST request to toggle favorite
- Updates icon styling:
  - Gray → Red: Added to favorites
  - Red → Gray: Removed from favorites
- Shows alert with confirmation message

## Performance Optimizations

1. **Compact JSON Format**: Single-letter keys reduce payload size
2. **Clustering**: Reduces DOM elements with many markers
3. **Lazy Loading**: Markers loaded after page render
4. **Single Fetch**: All points fetched in one request
5. **DOM Creation**: Uses native DOM methods, not innerHTML

## Error Handling

### API Fetch Failure
```javascript
.catch(error => {
    console.error('Error loading art locations:', error);
    alert('Failed to load art locations. Please refresh the page.');
});
```

### Favorite Toggle Failure
```javascript
.catch(error => {
    console.error('Error toggling favorite:', error);
    alert('Failed to update favorites. Please try again.');
});
```

## Browser Compatibility
- Modern browsers (ES6+)
- Requires:
  - `fetch` API
  - `Promise`
  - `const/let`
  - Arrow functions
  - Template literals
  - Geolocation API (for user location feature)

**Geolocation Requirements:**
- HTTPS (required in production; localhost works for development)
- User permission to access location
- Supported by all modern desktop and mobile browsers

## Related Files
- `templates/artinerary/home.html` - Template that loads this script
- `loc_detail/views.py` - API endpoints (`api_all_points`, `api_favorite_toggle`)
- `loc_detail/models.py` - Data models (PublicArt, UserFavoriteArt)

## Testing Checklist

**Geolocation:**
- [ ] Browser prompts for location permission on first load
- [ ] If allowed: map centers on user location at zoom 14
- [ ] Blue dot marker appears at user location with pulse animation
- [ ] Accuracy circle shows around user location
- [ ] "You are here" popup displays with accuracy radius
- [ ] If denied: map falls back to NYC center at zoom 11
- [ ] Location denial message appears and auto-hides after 5s

**Map Functionality:**
- [ ] Tiles load from OpenStreetMap
- [ ] Points fetch successfully from API
- [ ] Markers appear on map
- [ ] Clusters form with nearby markers
- [ ] Clicking cluster zooms in
- [ ] Popup shows correct information
- [ ] "View Details" navigates to correct page
- [ ] Heart icon toggles favorite status
- [ ] Heart changes color on toggle
- [ ] Alert shows on favorite toggle
- [ ] CSRF token included in POST requests
- [ ] Error messages display on failures

**Cross-Browser:**
- [ ] Works on Chrome/Edge (Chromium)
- [ ] Works on Firefox
- [ ] Works on Safari
- [ ] Works on mobile browsers (iOS/Android)

