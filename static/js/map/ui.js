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

