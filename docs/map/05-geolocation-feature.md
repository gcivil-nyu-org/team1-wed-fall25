# Geolocation Feature - User Location on Map

## Overview
The map automatically requests the user's current location when the page loads and centers the view on their position with a blue dot marker and accuracy circle, similar to Google Maps behavior.

## Implementation Date
October 17, 2025

## User Experience

### First Visit Flow
1. User navigates to `/artinerary/`
2. Browser displays permission prompt: "Allow [site] to access your location?"
3. **If User Allows:**
   - Map centers on their current location
   - Zoom level set to 14 (neighborhood view)
   - Blue dot marker appears at their position with pulse animation
   - Accuracy circle shows location precision
   - Popup displays: "You are here (±X meters)"
   - All 700+ art markers load with clustering
4. **If User Denies:**
   - Map falls back to NYC center (40.7128, -74.0060)
   - Zoom level set to 11 (city-wide view)
   - Blue message displays: "Location access not available. Showing NYC area instead."
   - Message auto-hides after 5 seconds
   - All 700+ art markers load with clustering

## Technical Implementation

### JavaScript Changes (`static/js/home_map.js`)

**Before:**
```javascript
const map = L.map('map').setView([40.7128, -74.0060], 11);
```

**After:**
```javascript
// Initialize without fixed view
const map = L.map('map');

// Request user location
map.locate({ setView: true, maxZoom: 14, enableHighAccuracy: true });

// Handle success
map.on('locationfound', function(e) {
    const radius = e.accuracy / 2;
    
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

// Handle error/denial
map.on('locationerror', function(e) {
    map.setView([40.7128, -74.0060], 11);
    // Show friendly message
});
```

### CSS Styling (`templates/artinerary/home.html`)

**Blue Dot Marker:**
- 20px diameter blue circle (#4285F4)
- White border (3px)
- Drop shadow for depth
- Pulse animation (2s loop)
- Positioned centered on location

**Accuracy Circle:**
- Google Maps blue (#4285F4)
- 10% fill opacity
- 1px border weight
- Radius matches GPS accuracy

**Location Notice:**
- Light blue background (#e3f2fd)
- Centered text
- Rounded corners (4px)
- Auto-hides after 5 seconds

## Geolocation API Details

### Browser API Used
```javascript
navigator.geolocation.getCurrentPosition()
```
Called internally by Leaflet's `map.locate()` method.

### Options
- `setView: true` - Automatically centers map on location
- `maxZoom: 14` - Caps zoom level (prevents too close)
- `enableHighAccuracy: true` - Uses GPS when available (better on mobile)

### Browser Requirements
1. **HTTPS Required:** Geolocation only works on secure connections
   - Exception: `localhost` works for development
   - Production must use HTTPS
2. **User Permission:** Browser shows permission prompt
   - Permission persists per domain
   - User can revoke in browser settings
3. **Browser Support:** All modern browsers (Chrome, Firefox, Safari, Edge)

## Privacy & Security

### What Data is Collected
- **Nothing is sent to the server**
- Location used entirely client-side
- Only used to center the map view
- Not stored, logged, or transmitted

### User Control
- Browser permission prompt on first access
- Can deny without losing functionality
- Can revoke permission anytime in browser settings
- Graceful fallback if denied

## Performance Impact

### Timing
- Location request: 0-3 seconds (varies by device/GPS)
- Runs in parallel with map initialization
- Does not block art markers from loading
- Tiles load immediately regardless of location status

### Battery Impact (Mobile)
- `enableHighAccuracy: true` uses GPS
- Higher accuracy but more battery usage
- Only requested once on page load
- Not continuously tracking

## Error Handling

### Common Errors
1. **PERMISSION_DENIED**: User clicked "Block"
   - Fallback: NYC center view
   - Message: "Location access not available"
2. **POSITION_UNAVAILABLE**: GPS/network issue
   - Fallback: NYC center view
   - Same message as permission denied
3. **TIMEOUT**: Location took too long
   - Fallback: NYC center view
   - Same graceful degradation

### Debugging
Console logs location errors:
```javascript
console.log('Location access denied or unavailable:', e.message);
```

Check browser console for:
- Geolocation permission status
- Accuracy values
- Error messages

## Testing Checklist

### Desktop Testing
- [ ] Chrome: Allow permission → blue dot appears
- [ ] Chrome: Block permission → NYC fallback, message shown
- [ ] Firefox: Test both allow/deny scenarios
- [ ] Safari: Test both allow/deny scenarios
- [ ] Edge: Test both allow/deny scenarios

### Mobile Testing
- [ ] Android Chrome: Location accuracy
- [ ] iOS Safari: Location accuracy
- [ ] Accuracy circle displays correctly
- [ ] Blue dot pulse animation smooth

### Permission States
- [ ] First visit: prompt appears
- [ ] After allow: no prompt on reload
- [ ] After block: no prompt, immediate fallback
- [ ] Clear permissions: prompt reappears

### Interaction Testing
- [ ] User location marker visible
- [ ] Can click user marker to see popup
- [ ] Art markers still load and cluster
- [ ] Can click art markers while user marker visible
- [ ] Zoom in/out maintains both marker types

## Browser Permission Reset

### Chrome/Edge
1. Click lock icon in address bar
2. Click "Site settings"
3. Change "Location" to "Ask"
4. Reload page

### Firefox
1. Click lock icon in address bar
2. Click "Clear permissions and cookies"
3. Reload page

### Safari
1. Preferences → Websites → Location
2. Find site, change to "Ask"
3. Reload page

## Future Enhancements

Potential improvements (not currently implemented):
1. **Continuous Tracking**: Update user position as they move
2. **"My Location" Button**: Manually re-center on user
3. **Distance Calculation**: Show art within X miles of user
4. **Directions**: Route from user to art location
5. **Compass Heading**: Show direction user is facing (mobile)
6. **Geofencing**: Notify when near favorite art pieces

## Rollback Procedure

If issues occur, revert to static NYC center:

1. Open `static/js/home_map.js`
2. Replace line 6:
   ```javascript
   const map = L.map('map');
   ```
   With:
   ```javascript
   const map = L.map('map').setView([40.7128, -74.0060], 11);
   ```
3. Remove lines 14-59 (geolocation handlers)
4. Commit and deploy

## Related Files
- `static/js/home_map.js` - Main implementation
- `templates/artinerary/home.html` - CSS styling and notice div
- `docs/map/03-js-behavior.md` - Technical documentation
- `docs/map/02-homepage-template.md` - Template documentation

## Resources
- [Leaflet Geolocation Docs](https://leafletjs.com/reference.html#map-locate)
- [MDN Geolocation API](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API)
- [Geolocation Security](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API/Using_the_Geolocation_API)

