# Backend API Endpoint: Favorite Toggle

## Overview
This document describes the `/loc_detail/api/favorite/<id>/toggle` endpoint that allows users to add or remove public art pieces from their favorites.

## Endpoint Details

### URL
```
POST /loc_detail/api/favorite/<art_id>/toggle
```

### Authentication
- **Required**: Yes (login required via `@login_required` decorator)
- Users must be authenticated to favorite artworks

### HTTP Method
- **Method**: POST only (enforced by `@require_POST` decorator)
- GET requests will return HTTP 405 Method Not Allowed

### URL Parameters
- `art_id` (integer): The primary key ID of the PublicArt object to toggle

### Response Format
Returns JSON indicating the current favorite status:

```json
{
  "favorited": true,
  "message": "Added to favorites"
}
```

or

```json
{
  "favorited": false,
  "message": "Removed from favorites"
}
```

### Implementation Details

**File**: `loc_detail/views.py`

```python
@login_required
@require_POST
def api_favorite_toggle(request, art_id):
    """API endpoint to toggle favorite status for an art piece"""
    art = get_object_or_404(PublicArt, id=art_id)
    
    # Check if already favorited
    favorite = UserFavoriteArt.objects.filter(user=request.user, art=art).first()
    
    if favorite:
        # Remove from favorites
        favorite.delete()
        favorited = False
        message = "Removed from favorites"
    else:
        # Add to favorites
        UserFavoriteArt.objects.create(user=request.user, art=art)
        favorited = True
        message = "Added to favorites"
    
    return JsonResponse({
        'favorited': favorited,
        'message': message
    })
```

### Database Model

**UserFavoriteArt Model** (`loc_detail/models.py`):
```python
class UserFavoriteArt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_art')
    art = models.ForeignKey(PublicArt, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['user', 'art']
        ordering = ['-added_at']
```

### Behavior
1. **First Click (Not Favorited)**:
   - Creates new `UserFavoriteArt` record
   - Links current user to the artwork
   - Returns `{"favorited": true, "message": "Added to favorites"}`

2. **Second Click (Already Favorited)**:
   - Deletes existing `UserFavoriteArt` record
   - Returns `{"favorited": false, "message": "Removed from favorites"}`

### Error Handling
- **404 Not Found**: If `art_id` doesn't exist in PublicArt table
- **405 Method Not Allowed**: If request method is not POST
- **Redirect to Login**: If user is not authenticated

### CSRF Protection
Requires CSRF token in POST request headers:
```javascript
headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrftoken
}
```

### Usage Examples

#### From Map Popup (home_map.js)
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
            heartElement.classList.add('favorited');
            alert('Location added to favourites');
        } else {
            heartElement.classList.remove('favorited');
            alert('Location removed from favourites');
        }
    });
}
```

#### From Detail Page (art_detail.html)
```javascript
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
        favoriteBtn.classList.add('favorited');
        alert('Location added to favourites');
    } else {
        favoriteBtn.classList.remove('favorited');
        alert('Location removed from favourites');
    }
});
```

### Database Constraints
- **Unique Constraint**: A user can only favorite a specific artwork once
- **Cascade Delete**: If user or artwork is deleted, favorite records are automatically removed

## Related Files
- `loc_detail/views.py` - View implementation
- `loc_detail/urls.py` - URL routing
- `loc_detail/models.py` - UserFavoriteArt model definition
- `static/js/home_map.js` - Map popup usage
- `templates/loc_detail/art_detail.html` - Detail page usage

