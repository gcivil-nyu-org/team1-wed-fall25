// Track selected items
let selectedLocations = [];
let selectedInvites = [];
const MAX_LOCATIONS = 5;

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Starting location autocomplete
const locationSearch = document.getElementById('location-search');
const locationResults = document.getElementById('location-results');
const startLocationSelect = document.getElementById('id_start_location');

if (locationSearch) {
    locationSearch.addEventListener('input', debounce(async function(e) {
        const term = e.target.value.trim();
        
        if (term.length < 2) {
            locationResults.style.display = 'none';
            return;
        }
        
        try {
            const response = await fetch(`/events/api/locations/search/?q=${encodeURIComponent(term)}`);
            const data = await response.json();
            
            if (data.results && data.results.length > 0) {
                locationResults.innerHTML = data.results.map(loc => `
                    <div class="autocomplete-item" data-id="${loc.id}" data-title="${loc.t}" data-artist="${loc.a}">
                        <strong>${loc.t}</strong> by ${loc.a}
                    </div>
                `).join('');
                locationResults.style.display = 'block';
            } else {
                locationResults.style.display = 'none';
            }
        } catch (error) {
            console.error('Error fetching locations:', error);
        }
    }, 300));
    
    locationResults.addEventListener('click', function(e) {
        const item = e.target.closest('.autocomplete-item');
        if (item) {
            const id = item.dataset.id;
            const title = item.dataset.title;
            
            // Set the select value
            startLocationSelect.value = id;
            locationSearch.value = `${title}`;
            locationResults.style.display = 'none';
        }
    });
}

// Additional locations autocomplete
const extraLocationSearch = document.getElementById('extra-location-search');
const extraLocationResults = document.getElementById('extra-location-results');
const locationsChips = document.getElementById('locations-chips');
const locationsCounter = document.getElementById('locations-counter');

if (extraLocationSearch) {
    extraLocationSearch.addEventListener('input', debounce(async function(e) {
        const term = e.target.value.trim();
        
        if (term.length < 2) {
            extraLocationResults.style.display = 'none';
            return;
        }
        
        try {
            const response = await fetch(`/events/api/locations/search/?q=${encodeURIComponent(term)}`);
            const data = await response.json();
            
            if (data.results && data.results.length > 0) {
                extraLocationResults.innerHTML = data.results.map(loc => `
                    <div class="autocomplete-item" data-id="${loc.id}" data-title="${loc.t}" data-artist="${loc.a}">
                        <strong>${loc.t}</strong> by ${loc.a}
                    </div>
                `).join('');
                extraLocationResults.style.display = 'block';
            } else {
                extraLocationResults.style.display = 'none';
            }
        } catch (error) {
            console.error('Error fetching locations:', error);
        }
    }, 300));
    
    extraLocationResults.addEventListener('click', function(e) {
        const item = e.target.closest('.autocomplete-item');
        if (item) {
            const id = item.dataset.id;
            const title = item.dataset.title;
            const artist = item.dataset.artist;
            
            if (selectedLocations.length >= MAX_LOCATIONS) {
                alert(`Maximum ${MAX_LOCATIONS} locations allowed`);
                return;
            }
            
            if (selectedLocations.some(loc => loc.id === id)) {
                alert('Location already added');
                return;
            }
            
            selectedLocations.push({ id, title, artist });
            renderLocationChips();
            
            extraLocationSearch.value = '';
            extraLocationResults.style.display = 'none';
        }
    });
}

function renderLocationChips() {
    locationsChips.innerHTML = selectedLocations.map((loc, index) => `
        <div class="chip">
            ${loc.title}
            <span class="chip-remove" data-index="${index}">&times;</span>
        </div>
    `).join('');
    
    locationsCounter.textContent = `${selectedLocations.length}/${MAX_LOCATIONS}`;
    
    // Add event listeners to remove buttons
    locationsChips.querySelectorAll('.chip-remove').forEach(btn => {
        btn.addEventListener('click', function() {
            const index = parseInt(this.dataset.index);
            selectedLocations.splice(index, 1);
            renderLocationChips();
        });
    });
}

// User invite autocomplete
const userSearch = document.getElementById('user-search');
const userResults = document.getElementById('user-results');
const invitesChips = document.getElementById('invites-chips');

if (userSearch) {
    userSearch.addEventListener('input', debounce(async function(e) {
        const term = e.target.value.trim();
        
        if (term.length < 2) {
            userResults.style.display = 'none';
            return;
        }
        
        try {
            const response = await fetch(`/events/api/users/search/?q=${encodeURIComponent(term)}`);
            const data = await response.json();
            
            if (data.results && data.results.length > 0) {
                userResults.innerHTML = data.results.map(user => `
                    <div class="autocomplete-item" data-id="${user.id}" data-username="${user.u}">
                        ${user.u}
                    </div>
                `).join('');
                userResults.style.display = 'block';
            } else {
                userResults.style.display = 'none';
            }
        } catch (error) {
            console.error('Error fetching users:', error);
        }
    }, 300));
    
    userResults.addEventListener('click', function(e) {
        const item = e.target.closest('.autocomplete-item');
        if (item) {
            const id = item.dataset.id;
            const username = item.dataset.username;
            
            if (selectedInvites.some(user => user.id === id)) {
                alert('User already invited');
                return;
            }
            
            selectedInvites.push({ id, username });
            renderInviteChips();
            
            userSearch.value = '';
            userResults.style.display = 'none';
        }
    });
}

function renderInviteChips() {
    invitesChips.innerHTML = selectedInvites.map((user, index) => `
        <div class="chip">
            ${user.username}
            <span class="chip-remove" data-index="${index}">&times;</span>
        </div>
    `).join('');
    
    // Add event listeners to remove buttons
    invitesChips.querySelectorAll('.chip-remove').forEach(btn => {
        btn.addEventListener('click', function() {
            const index = parseInt(this.dataset.index);
            selectedInvites.splice(index, 1);
            renderInviteChips();
        });
    });
}

// Form submission - add hidden inputs
const form = document.getElementById('create-event-form');
if (form) {
    form.addEventListener('submit', function(e) {
        // Remove any existing hidden inputs
        form.querySelectorAll('input[name="locations[]"], input[name="invites[]"]').forEach(input => {
            input.remove();
        });
        
        // Add location hidden inputs
        selectedLocations.forEach(loc => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'locations[]';
            input.value = loc.id;
            form.appendChild(input);
        });
        
        // Add invite hidden inputs
        selectedInvites.forEach(user => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'invites[]';
            input.value = user.id;
            form.appendChild(input);
        });
    });
}

// Close autocomplete when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('.location-search-container') && !e.target.closest('.user-search-container')) {
        locationResults.style.display = 'none';
        extraLocationResults.style.display = 'none';
        userResults.style.display = 'none';
    }
});

