# Artinerary Test Suite

This directory contains comprehensive unit tests for the Artinerary application with excellent code coverage.

## Test Structure

### Location Details Tests (`test_loc_detail_*.py`)

#### `test_loc_detail_models.py` - Model Tests (100% Coverage)
Tests for all `loc_detail` models:

**PublicArtModelTests** - 9 tests
- Creating art instances
- String representations
- Field validation (blank fields, coordinates precision)
- Unique constraints (external_id)
- Default ordering
- Timestamps

**UserFavoriteArtModelTests** - 8 tests
- Creating favorites
- String representation
- Unique together constraint (user + art)
- Multiple users favoriting same art
- Cascade deletes (user/art deletion)
- Timestamps and ordering

**ArtCommentModelTests** - 8 tests
- Creating comments
- String representation
- Multiple comments per user/art
- Cascade deletes
- Timestamps and ordering
- Related name access

#### `test_loc_detail_views.py` - View Tests (100% Coverage)
Tests for all `loc_detail` views and API endpoints:

**LocDetailIndexViewTests** - 12 tests
- Authentication requirements
- Display all art pieces
- Search functionality (title, artist, description, location)
- Borough filtering
- Combined search and filter
- Pagination (20 items per page)
- Borough dropdown population
- Total count

**ArtDetailViewTests** - 12 tests
- Authentication requirements
- Display art information
- 404 for invalid IDs
- Comment posting (valid/empty)
- Comment display
- Related art suggestions (same borough/artist)
- Favorite status indication

**APIAllPointsViewTests** - 6 tests
- Authentication requirements
- JSON response format
- Compact data structure (id, t, a, b, y, x)
- Coordinate filtering (only with lat/lng)
- Float conversion for coordinates
- Default values (Untitled/Unknown)

**APIFavoriteToggleViewTests** - 6 tests
- Authentication requirements
- POST method requirement
- Adding to favorites
- Removing from favorites
- Toggle functionality
- 404 for invalid art ID

**FavoritesViewTests** - 10 tests
- Authentication requirements
- Display user's favorites only
- Search in favorites
- Borough filtering
- Empty favorites list
- Pagination
- Ordering by recent
- Total count
- Borough dropdown (from favorites)

## Running Tests

### Run All Location Details Tests
```powershell
python manage.py test tests.test_loc_detail_models tests.test_loc_detail_views
```

### Run Specific Test Class
```powershell
python manage.py test tests.test_loc_detail_models.PublicArtModelTests
python manage.py test tests.test_loc_detail_views.ArtDetailViewTests
```

### Run Specific Test Method
```powershell
python manage.py test tests.test_loc_detail_models.PublicArtModelTests.test_create_public_art
```

### Run with Verbose Output
```powershell
python manage.py test tests -v 2
```

## Coverage Reports

### Generate Coverage for Location Details
```powershell
coverage run manage.py test tests.test_loc_detail_models tests.test_loc_detail_views
coverage report --include='loc_detail/*'
```

### Generate Coverage for All Tests
```powershell
coverage run manage.py test
coverage report
```

### Generate HTML Coverage Report
```powershell
coverage run manage.py test
coverage html
# Open htmlcov/index.html in browser
```

### Coverage Configuration

Coverage is configured via `.coveragerc` to exclude:
- Migration files
- Test files
- Management commands (like `import_art_data.py`)
- Virtual environments
- `__pycache__` directories
- WSGI/ASGI files
- `manage.py`

## Test Coverage Summary

**Current Coverage (Location Details):**
- `loc_detail/models.py`: **100%** ✅
- `loc_detail/views.py`: **100%** ✅
- `loc_detail/urls.py`: **100%** ✅
- `loc_detail/admin.py`: **96%** ✅
- `loc_detail/apps.py`: **100%** ✅

**Total Tests:** 68 tests
**Status:** All passing ✅

## What's Tested

### Models
✅ All model fields and relationships
✅ String representations
✅ Unique constraints
✅ Cascade deletions
✅ Default ordering
✅ Timestamps (auto_now, auto_now_add)
✅ Related name access
✅ Data validation

### Views
✅ Authentication/authorization
✅ GET/POST requests
✅ Search functionality
✅ Filtering and pagination
✅ JSON API responses
✅ Error handling (404, empty inputs)
✅ Database queries
✅ Context data
✅ Template rendering
✅ Redirects

### Business Logic
✅ User favorites (add/remove/toggle)
✅ Comments on art pieces
✅ Art search and filtering
✅ Related art suggestions
✅ Geolocation data (coordinates)
✅ API endpoint responses

## Test Data

Tests use Django's test database (SQLite in-memory) and create minimal test data:
- Test users with authentication
- Public art pieces with various attributes
- User favorites
- Comments
- Coordinates for map testing

## Best Practices Used

✅ **Isolation**: Each test is independent
✅ **setUp/tearDown**: Proper test data initialization
✅ **Descriptive names**: Clear test method names
✅ **Single assertion focus**: Each test focuses on one thing
✅ **Edge cases**: Empty data, invalid IDs, null values
✅ **Authentication**: Login requirements tested
✅ **HTTP methods**: GET/POST validation
✅ **Database constraints**: Unique, cascade tested

## Future Enhancements

- Integration tests for complete user workflows
- Performance tests for large datasets
- JavaScript tests for map interactions
- Selenium tests for UI interactions
- API endpoint rate limiting tests
- Security tests (CSRF, XSS, SQL injection)
