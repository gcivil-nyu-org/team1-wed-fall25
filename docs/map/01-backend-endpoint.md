# Backend API Endpoint: All Points

## Overview
This document describes the `/loc_detail/api/points/all` endpoint that provides all public art location data for the interactive map.

## Endpoint Details

### URL
```
GET /loc_detail/api/points/all
```

### Authentication
- **Required**: Yes (login required via `@login_required` decorator)
- Users must be authenticated to access this endpoint

### Response Format
Returns JSON with a compact array of art location points:

```json
{
  "points": [
    {
      "id": 1,
      "t": "Art Title",
      "a": "Artist Name",
      "b": "Manhattan",
      "y": 40.7128,
      "x": -74.0060
    },
    ...
  ]
}
```

### Field Mapping
- `id`: Primary key of the PublicArt object
- `t`: Title of the artwork (defaults to "Untitled")
- `a`: Artist name (defaults to "Unknown")
- `b`: Borough name (empty string if not set)
- `y`: Latitude (decimal)
- `x`: Longitude (decimal)

### Implementation Details

**File**: `loc_detail/views.py`

```python
@login_required
def api_all_points(request):
    """API endpoint returning all public art points as compact JSON"""
    # Fetch all art with valid coordinates
    art_points = PublicArt.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).values('id', 'title', 'artist_name', 'borough', 'latitude', 'longitude')[:5000]
    
    # Compact format: {id, t(itle), a(rtist), b(orough), y(lat), x(lng)}
    points = [
        {
            'id': art['id'],
            't': art['title'] or 'Untitled',
            'a': art['artist_name'] or 'Unknown',
            'b': art['borough'] or '',
            'y': float(art['latitude']),
            'x': float(art['longitude'])
        }
        for art in art_points
    ]
    
    return JsonResponse({'points': points})
```

### Performance Considerations
- **Limit**: Capped at 5000 points to prevent excessive data transfer
- **Filtering**: Only returns records with valid latitude/longitude coordinates
- **Compact Format**: Uses single-letter keys to minimize JSON payload size
- **Query Optimization**: Uses `.values()` to fetch only required fields

### Database Query
```python
PublicArt.objects.filter(
    latitude__isnull=False,
    longitude__isnull=False
).values('id', 'title', 'artist_name', 'borough', 'latitude', 'longitude')[:5000]
```

### Error Handling
- Returns empty array if no points exist: `{"points": []}`
- Requires user authentication; redirects to login if not authenticated

### Usage
Frontend JavaScript fetches this endpoint on map initialization:
```javascript
fetch('/loc_detail/api/points/all')
    .then(response => response.json())
    .then(data => {
        console.log(`Loaded ${data.points.length} art locations`);
        // Process points...
    });
```

## Related Files
- `loc_detail/views.py` - View implementation
- `loc_detail/urls.py` - URL routing
- `loc_detail/models.py` - PublicArt model definition
- `static/js/home_map.js` - Frontend consumer

