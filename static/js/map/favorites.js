/**
 * Favorites Management
 * Handles favorite toggling and API integration
 */

import { MAP_CONFIG } from './config.js';

/**
 * Get CSRF token from cookies for Django POST requests
 * @param {string} name - Cookie name
 * @returns {string|null} Cookie value or null
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

const csrftoken = getCookie('csrftoken');

/**
 * Toggle favorite status for an art piece
 * @param {number} artId - Art piece ID
 * @param {HTMLElement} heartElement - Heart icon element to update
 */
export function toggleFavorite(artId, heartElement) {
    fetch(`${MAP_CONFIG.api.favoriteToggle}/${artId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.favorited) {
            heartElement.classList.remove('not-favorited');
            heartElement.classList.add('favorited');
            alert('Location added to favourites');
        } else {
            heartElement.classList.remove('favorited');
            heartElement.classList.add('not-favorited');
            alert('Location removed from favourites');
        }
    })
    .catch(error => {
        console.error('Error toggling favorite:', error);
        alert('Failed to update favorites. Please try again.');
    });
}

