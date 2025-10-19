# Where is the Map? 🗺️

## Quick Answer

The map is located at: **`http://127.0.0.1:8000/artinerary/`**

## Step-by-Step Access

### 1. Start the Development Server
```bash
# Navigate to project directory
cd d:\STUFF\NYU_Coursework\SE\Project

# Activate virtual environment
.\venv\Scripts\activate

# Run server
python manage.py runserver
```

### 2. Login First
**Important**: You MUST be logged in to see the map!

Navigate to: `http://127.0.0.1:8000/accounts/login/`

### 3. Access the Map
After logging in, go to: **`http://127.0.0.1:8000/artinerary/`**

## Alternative Access Points

### From Navigation Bar
Once logged in, look for these links in the top navigation:
- Click **"Browse Art"** → Goes to `/loc_detail/` (list view)
- Or directly navigate to `/artinerary/` for the map view

### From Base Template
The navigation should have:
```
Artinerary | Browse Art | [User Menu] | Logout
```

## What You Should See

### The Map Page Should Display:
1. **Header**: "NYC Public Art Map"
2. **Subheader**: "Explore public art installations across New York City"
3. **Full-screen interactive map** showing:
   - NYC area centered
   - Clustered markers (numbered circles)
   - Blue markers for individual art pieces

### When You Click a Cluster:
- It zooms in or expands to show individual markers

### When You Click a Marker:
A popup appears with:
- **Title** of the artwork (bold)
- **Artist name** (gray)
- **Borough** (light gray)
- **Green "View Details" button**
- **Gray heart icon** ❤️

### When You Click the Heart:
- Turns **RED** ❤️
- Alert: "Location added to favourites"
- Click again to remove (turns gray)

### When You Click "View Details":
- Navigates to: `/loc_detail/art/<id>/`
- Shows full artwork information
- Has a favorite button there too

## Troubleshooting

### "I don't see the map, just a blank page"
**Causes**:
1. **Not logged in** → Go to `/accounts/login/` first
2. **JavaScript error** → Check browser console (F12)
3. **No data** → Run: `python manage.py import_art_data` to populate the database

### "I see the map but no markers"
**Causes**:
1. **No data in database** → Run the import command
2. **API error** → Check browser console Network tab
3. **Authentication issue** → Logout and login again

### "Map loads but markers don't appear"
**Check**:
1. Open browser console (F12)
2. Look for error messages
3. Check Network tab for `/loc_detail/api/points/all` call
4. Should return JSON with `points` array

### "I get a 404 error"
**Verify**:
1. URL is exactly: `http://127.0.0.1:8000/artinerary/` (with trailing slash)
2. Server is running
3. You're on the correct branch: `extensive_2`

## URL Structure Quick Reference

```
/accounts/login/              → Login page
/accounts/signup/             → Signup page
/artinerary/                  → 🗺️ MAP HOMEPAGE (THIS IS IT!)
/loc_detail/                  → List view of all art
/loc_detail/art/157/          → Individual art detail page
/loc_detail/api/points/all    → JSON API (map data)
/loc_detail/api/favorite/157/toggle → Favorite toggle API
```

## File Locations (For Debugging)

```
Backend:
- artinerary/views.py         → Map view handler
- artinerary/urls.py          → Routes /artinerary/ to view
- loc_detail/views.py         → API endpoints

Frontend:
- templates/artinerary/home.html → Map page template
- static/js/home_map.js       → Map JavaScript logic

URLs:
- core/urls.py                → Includes artinerary/ route
```

## Quick Test Commands

```bash
# Activate venv
.\venv\Scripts\activate

# Check system
python manage.py check

# Import data (if needed)
python manage.py import_art_data

# Run server
python manage.py runserver

# Then visit: http://127.0.0.1:8000/artinerary/
```

## Expected Behavior Video Guide

1. **Load** → Full screen map of NYC
2. **Wait 1-2 seconds** → Markers appear as clusters
3. **Click cluster** → Zooms in
4. **Click marker** → Popup opens
5. **Click heart** → Turns red, alert shows
6. **Click "View Details"** → Goes to detail page

## Still Can't Find It?

The map is implemented in these specific files:
- **View**: `artinerary/views.py` - Line 6-8
- **Template**: `templates/artinerary/home.html` - Full file
- **JavaScript**: `static/js/home_map.js` - Full file
- **URL**: `artinerary/urls.py` - Line 7 (index route)

Make sure you're accessing `/artinerary/` NOT `/loc_detail/`!

---

**TL;DR**: 
1. Login at `/accounts/login/`
2. Go to `/artinerary/`
3. See map! 🗺️

