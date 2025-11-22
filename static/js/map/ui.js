/**
 * UI Components
 * Handles creation of map UI elements like popups and markers
 */

import { toggleFavorite } from './favorites.js';

/**
 * Create popup content for an art marker
 * @param {Object} point - Art point data containing id, title, artist, borough
 * @returns {HTMLElement} Popup content as DOM element
 */
export function createPopupContent(point) {
    // console.log('Creating popup for:', point.t);
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

    // Borough
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
    detailBtn.className = 'btn btn-primary';
    detailBtn.textContent = 'View Details';
    actions.appendChild(detailBtn);

    // Add to Itinerary button
    const itineraryBtn = document.createElement('button');
    itineraryBtn.className = 'btn btn-outline-primary';
    itineraryBtn.innerHTML = '<i class="fas fa-route"></i>';
    itineraryBtn.title = 'Add to Itinerary';
    itineraryBtn.onclick = function (e) {
        e.preventDefault();
        openItineraryModal(point.id, point.t);
    };
    actions.appendChild(itineraryBtn);
    // console.log('Added itinerary button to popup');

    // Heart icon for favorites
    const heart = document.createElement('span');
    heart.className = 'favorite-heart not-favorited';
    heart.innerHTML = '&#10084;';
    heart.title = 'Add to favorites';
    heart.onclick = function (e) {
        e.preventDefault();
        toggleFavorite(point.id, heart);
    };
    actions.appendChild(heart);

    popupDiv.appendChild(actions);

    return popupDiv;
}

/**
 * Open modal for adding location to itinerary
 * @param {number} locationId - ID of the location to add
 * @param {string} locationTitle - Title of the location
 */
function openItineraryModal(locationId, locationTitle) {
    // Check if modal already exists, if not create it
    let modal = document.getElementById('itinerary-modal');
    if (!modal) {
        modal = createItineraryModal();
        document.body.appendChild(modal);
    }

    // Update modal content
    document.getElementById('modal-location-title').textContent = locationTitle;
    document.getElementById('modal-location-id').value = locationId;

    // Load user's itineraries
    loadUserItineraries();

    // Show modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
}

/**
 * Create the itinerary modal HTML structure
 * @returns {HTMLElement} Modal element
 */
function createItineraryModal() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'itinerary-modal';
    modal.tabIndex = -1;
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title">
                        <i class="fas fa-route me-2"></i>Add to Itinerary
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p class="mb-3">
                        <strong>Location:</strong> <span id="modal-location-title"></span>
                    </p>
                    <input type="hidden" id="modal-location-id">
                    
                    <div class="mb-3">
                        <label class="form-label">Choose an option:</label>
                        <div class="form-check">
                            <input class="form-check-input" type="radio" name="itinerary-option" 
                                   id="option-existing" value="existing" checked>
                            <label class="form-check-label" for="option-existing">
                                Add to existing itinerary
                            </label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="radio" name="itinerary-option" 
                                   id="option-new" value="new">
                            <label class="form-check-label" for="option-new">
                                Create new itinerary
                            </label>
                        </div>
                    </div>
                    
                    <div id="existing-itinerary-section" class="mb-3">
                        <label for="existing-itinerary-select" class="form-label">Select Itinerary</label>
                        <select class="form-select" id="existing-itinerary-select">
                            <option value="">Loading...</option>
                        </select>
                    </div>
                    
                    <div id="new-itinerary-section" class="mb-3" style="display: none;">
                        <label for="new-itinerary-title" class="form-label">New Itinerary Title</label>
                        <input type="text" class="form-control" id="new-itinerary-title" 
                               placeholder="Enter itinerary title">
                    </div>
                    
                    <div id="modal-message" class="alert" style="display: none;"></div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" id="btn-save-to-itinerary">
                        <i class="fas fa-plus me-1"></i>Add to Itinerary
                    </button>
                </div>
            </div>
        </div>
    `;

    // Add event listeners
    modal.querySelector('#option-existing').addEventListener('change', function () {
        document.getElementById('existing-itinerary-section').style.display = 'block';
        document.getElementById('new-itinerary-section').style.display = 'none';
    });

    modal.querySelector('#option-new').addEventListener('change', function () {
        document.getElementById('existing-itinerary-section').style.display = 'none';
        document.getElementById('new-itinerary-section').style.display = 'block';
    });

    modal.querySelector('#btn-save-to-itinerary').addEventListener('click', saveToItinerary);

    return modal;
}

/**
 * Load user's itineraries and populate the dropdown
 */
async function loadUserItineraries() {
    const select = document.getElementById('existing-itinerary-select');

    try {
        const response = await fetch('/itineraries/api/user-itineraries/');
        const data = await response.json();

        if (data.itineraries.length === 0) {
            select.innerHTML = '<option value="">No itineraries yet</option>';
            document.getElementById('option-new').checked = true;
            document.getElementById('existing-itinerary-section').style.display = 'none';
            document.getElementById('new-itinerary-section').style.display = 'block';
        } else {
            select.innerHTML = '<option value="">-- Select an itinerary --</option>' +
                data.itineraries.map(itin =>
                    `<option value="${itin.id}">${itin.title} (${itin.stop_count} stops)</option>`
                ).join('');
        }
    } catch (error) {
        console.error('Error loading itineraries:', error);
        select.innerHTML = '<option value="">Error loading itineraries</option>';
    }
}

/**
 * Save location to selected or new itinerary
 */
async function saveToItinerary() {
    const locationId = document.getElementById('modal-location-id').value;
    const option = document.querySelector('input[name="itinerary-option"]:checked').value;
    const messageDiv = document.getElementById('modal-message');
    const saveBtn = document.getElementById('btn-save-to-itinerary');

    // Collect form data
    const formData = new FormData();
    formData.append('location_id', locationId);

    if (option === 'existing') {
        const itineraryId = document.getElementById('existing-itinerary-select').value;
        if (!itineraryId) {
            showMessage('Please select an itinerary', 'danger');
            return;
        }
        formData.append('itinerary_id', itineraryId);
    } else {
        const title = document.getElementById('new-itinerary-title').value.trim();
        if (!title) {
            showMessage('Please enter a title for the new itinerary', 'danger');
            return;
        }
        formData.append('new_itinerary_title', title);
    }

    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken);
    }

    // Disable button while saving
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Adding...';

    try {
        const response = await fetch('/itineraries/api/add-to-itinerary/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        const data = await response.json();

        if (data.success) {
            showMessage(data.message + ' <a href="' + data.itinerary_url + '">View Itinerary</a>', 'success');
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('itinerary-modal')).hide();
            }, 2000);
        } else {
            showMessage(data.error, 'danger');
        }
    } catch (error) {
        console.error('Error saving to itinerary:', error);
        showMessage('An error occurred. Please try again.', 'danger');
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-plus me-1"></i>Add to Itinerary';
    }
}

/**
 * Show message in modal
 * @param {string} message - Message to display
 * @param {string} type - Bootstrap alert type (success, danger, etc.)
 */
function showMessage(message, type) {
    const messageDiv = document.getElementById('modal-message');
    messageDiv.className = `alert alert-${type}`;
    messageDiv.innerHTML = message;
    messageDiv.style.display = 'block';

    if (type === 'success') {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    }
}

/**
 * Get cookie value by name
 * @param {string} name - Cookie name
 * @returns {string|null} Cookie value
 */
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
