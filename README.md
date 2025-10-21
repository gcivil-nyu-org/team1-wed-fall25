# Artinerary

Artinerary is a Django web application for exploring NYC public art installations. Users can browse art on an interactive map, search by location or artist, save favorites, and leave comments.

Main: 
[![build status](https://app.travis-ci.com/gcivil-nyu-org/team1-wed-fall25.svg?token=2YAzE5PLqmscpsxcrmuV&branch=main)](https://app.travis-ci.com/gcivil-nyu-org/team1-wed-fall25.svg?token=2YAzE5PLqmscpsxcrmuV&branch=main) [![Coverage Status](https://coveralls.io/repos/github/gcivil-nyu-org/team1-wed-fall25/badge.svg?branch=main)](https://coveralls.io/github/gcivil-nyu-org/team1-wed-fall25?branch=main)

Develop:
[![build status](https://app.travis-ci.com/gcivil-nyu-org/team1-wed-fall25.svg?token=2YAzE5PLqmscpsxcrmuV&branch=develop)](https://app.travis-ci.com/gcivil-nyu-org/team1-wed-fall25.svg?token=2YAzE5PLqmscpsxcrmuV&branch=develop) [![Coverage Status](https://coveralls.io/repos/github/gcivil-nyu-org/team1-wed-fall25/badge.svg?branch=develop)](https://coveralls.io/github/gcivil-nyu-org/team1-wed-fall25?branch=develop)

## Testing

Comprehensive unit tests are available in the `tests/` directory

### Run Tests
```bash
python manage.py test
```

### Run Specific Tests
```bash
python manage.py test tests.test_loc_detail_models
python manage.py test tests.test_loc_detail_views
```

### Generate Coverage Report
```bash
coverage run manage.py test
coverage report
```

See `tests/README.md` for detailed testing documentation.
>>>>>>> develop
