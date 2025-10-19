# Map Module Architecture

## Overview
This directory contains the modular architecture for the Artinerary interactive map. The code is organized into focused, single-responsibility modules for maintainability and scalability.

## File Structure

```
static/js/map/
├── config.js          # Configuration constants and settings
├── layers.js          # Tile layer management
├── geolocation.js     # User location handling
├── markers.js         # Art marker management and clustering
├── favorites.js       # Favorites API integration
├── ui.js              # UI components (popups, markers)
└── init.js            # Main orchestrator and entry point
```

## Module Responsibilities

### config.js (~40 lines)
- **Purpose**: Central configuration management
- **Exports**: `MAP_CONFIG` object
- **Contains**:
  - Map center coordinates
  - NYC bounds constants
  - Default zoom levels
  - API endpoints
  - Marker clustering options
  - User marker styling

### layers.js (~40 lines)
- **Purpose**: Tile layer management
- **Exports**: `createTileLayers()`, `addLayerControl()`
- **Responsibilities**:
  - Define available tile layer sources (Vibrant, Streets)
  - Add layer control UI to map
  - Set default layer

### geolocation.js (~95 lines)
- **Purpose**: User location detection and handling
- **Exports**: `GeolocationManager` class
- **Responsibilities**:
  - Request user's current location
  - Handle successful location detection
  - Create user location marker and accuracy circle
  - Handle location errors/denials
  - Show location notices to user
  - Track location state

### markers.js (~80 lines)
- **Purpose**: Art marker management
- **Exports**: `MarkerManager` class
- **Responsibilities**:
  - Fetch art points from API
  - Create marker clusters
  - Bind popups to markers
  - Intelligent bounds fitting (respects user location and NYC bounds)
  - Handle marker loading errors

### favorites.js (~60 lines)
- **Purpose**: Favorites functionality
- **Exports**: `toggleFavorite()` function
- **Responsibilities**:
  - CSRF token handling for Django
  - Toggle favorite API calls
  - Update UI on success/failure
  - Error handling and user feedback

### ui.js (~60 lines)
- **Purpose**: UI component creation
- **Exports**: `createPopupContent()` function
- **Responsibilities**:
  - Generate popup HTML for art markers
  - Create action buttons (View Details, Favorites)
  - Handle popup interactions

### init.js (~55 lines)
- **Purpose**: Main orchestrator
- **Exports**: `initializeMap()` function
- **Responsibilities**:
  - Coordinate all modules
  - Initialize map with proper sequence
  - Handle initialization errors
  - Expose public API

## Usage

### Basic Implementation
```javascript
import { initializeMap } from './map/init.js';

// Initialize the map
initializeMap()
    .then(({ map, geoManager, markerManager }) => {
        console.log('Map ready!');
        // Optional: Use returned instances for advanced features
    })
    .catch(error => {
        console.error('Map initialization failed:', error);
    });
```

### In HTML Template
```html
<script type="module">
    import { initializeMap } from "{% static 'js/map/init.js' %}";
    initializeMap().catch(console.error);
</script>
```

## Adding New Features

### 1. Adding a new tile layer
**Edit**: `layers.js`
```javascript
export function createTileLayers() {
    return {
        "Vibrant": L.tileLayer(...),
        "Streets": L.tileLayer(...),
        "NewLayer": L.tileLayer(...) // Add here
    };
}
```

### 2. Adding new marker functionality
**Edit**: `markers.js`
```javascript
export class MarkerManager {
    // Add new methods here
    filterMarkersByBorough(borough) { ... }
}
```

### 3. Adding new UI components
**Edit**: `ui.js`
```javascript
export function createCustomPopup(point) { ... }
```

### 4. Adding new configuration
**Edit**: `config.js`
```javascript
export const MAP_CONFIG = {
    // Add new config values
    newFeature: { ... }
};
```

## Development Workflow

### Local Development
1. Edit files in `static/js/map/`
2. Django serves files from `static/` in development (DEBUG=True)
3. Refresh browser to see changes
4. No need to run `collectstatic` during development

### Production Deployment
```bash
# Collect static files for production
python manage.py collectstatic --noinput

# Files will be copied to staticfiles/js/map/
# Production serves from staticfiles/ (DEBUG=False)
```

## Best Practices

1. **Single Responsibility**: Each module should do ONE thing well
2. **No Cross-Dependencies**: Modules should only depend on config.js
3. **Clear Exports**: Export only what's needed publicly
4. **Error Handling**: Always catch and log errors
5. **Documentation**: Comment complex logic
6. **File Size**: Keep modules under 100 lines when possible

## Troubleshooting

### Map not loading
- Check browser console for errors
- Verify Leaflet library is loaded before map modules
- Ensure `<div id="map"></div>` exists in HTML

### Markers not appearing
- Check API endpoint is returning data
- Verify marker coordinates are valid
- Check console for API errors

### Geolocation not working
- Ensure HTTPS (required for geolocation API)
- Check browser permissions
- Verify fallback to Manhattan works

### Favorites not toggling
- Check CSRF token is present
- Verify API endpoint is correct
- Check user authentication status

## Testing

### Manual Testing Checklist
- [ ] Map initializes with Manhattan view
- [ ] Geolocation prompt appears
- [ ] User location centers map correctly
- [ ] Markers load and cluster
- [ ] Layer switcher works
- [ ] Popups display correctly
- [ ] Favorites toggle works
- [ ] Error messages display properly

## Performance Considerations

- **Lazy Loading**: Geolocation and markers load asynchronously
- **Clustering**: Markers are clustered for performance with 1000+ points
- **Debouncing**: Consider adding debouncing for frequent operations
- **Memory**: No memory leaks; event listeners properly managed

## Future Enhancements

Potential additions that fit this architecture:
- Search/filter functionality (new `search.js` module)
- Route planning (new `routing.js` module)
- Custom marker icons (extend `ui.js`)
- Map animations (new `animations.js` module)
- Advanced clustering (extend `markers.js`)

## Questions?

For implementation questions or bug reports, refer to:
- Main docs: `docs/map/00-implementation-summary.md`
- Django views: `artinerary/views.py`
- API endpoints: `loc_detail/views.py`

