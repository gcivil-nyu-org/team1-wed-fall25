// Map initialization and functionality for Artinerary homepage
(function() {
    'use strict';

    // Initialize map centered on NYC
    const map = L.map('map').setView([40.7128, -74.0060], 11);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    // Create marker cluster group
    const markers = L.markerClusterGroup({
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true
    });

    // CSRF token helper for POST requests
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

    // Toggle favorite function
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

    // Create popup content for a marker
    function createPopupContent(point) {
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

    // Fetch all points and add to map
    fetch('/loc_detail/api/points/all')
        .then(response => response.json())
        .then(data => {
            console.log(`Loaded ${data.points.length} art locations`);
            
            data.points.forEach(point => {
                const marker = L.marker([point.y, point.x]);
                const popupContent = createPopupContent(point);
                marker.bindPopup(popupContent);
                markers.addLayer(marker);
            });
            
            // Add marker cluster to map
            map.addLayer(markers);
            
            // Fit bounds to show all markers
            if (data.points.length > 0) {
                map.fitBounds(markers.getBounds(), { padding: [50, 50] });
            }
        })
        .catch(error => {
            console.error('Error loading art locations:', error);
            alert('Failed to load art locations. Please refresh the page.');
        });
})();

