// Map initialization and functionality for Artinerary homepage
(function() {
    'use strict';

    // Initialize map without fixed view - let geolocation set it
    const map = L.map('map').setView([40.7831, -73.9712], 12);

    
    // Define 4 different tile layer options (using free, no-API-key providers)
    const baseMaps = {
        "Vibrant": L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }),
        "Watercolor": L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/watercolor/{z}/{x}/{y}.jpg', {
            attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 16
        }),
        "Streets": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }),
        "Terrain": L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
            attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
            maxZoom: 17
        })
    };

    // Add the default layer (Vibrant for colorful modern look)
    baseMaps["Vibrant"].addTo(map);

    // Add layer control to allow users to switch between styles
    L.control.layers(baseMaps).addTo(map);

    // Track geolocation state to prevent fitBounds from overriding user location
    let userLocated = false;

    // Request user's current location
    map.locate({ setView: true, maxZoom: 14, enableHighAccuracy: true });

    // Handle successful location detection
    let userMarker = null;
    let userCircle = null;
    map.on('locationfound', function(e) {
        userLocated = true;
        const radius = e.accuracy / 2;
        
        // Create blue dot marker (Google Maps style)
        const userIcon = L.divIcon({
            className: 'user-location-marker',
            html: '<div class="user-dot"></div>',
            iconSize: [20, 20]
        });
        
        userMarker = L.marker(e.latlng, { icon: userIcon }).addTo(map)
            .bindPopup("You are here (±" + Math.round(radius) + " meters)")
            .openPopup();
        
        // Add accuracy circle
        userCircle = L.circle(e.latlng, radius, {
            color: '#4285F4',
            fillColor: '#4285F4',
            fillOpacity: 0.1,
            weight: 1
        }).addTo(map);

        // Ensure user view wins over any later operations (like fitBounds)
        map.setView(e.latlng, 14);
    });

    // Handle location error or denial
    map.on('locationerror', function(e) {
        userLocated = false;
        console.log('Location access denied or unavailable:', e.message);
        // Keep Manhattan default (already set in initialization)
        
        // Show message to user
        const notice = document.getElementById('location-notice');
        const noticeText = document.getElementById('notice-text');
        if (notice && noticeText) {
            noticeText.textContent = 'Location access not available. Showing NYC area instead.';
            notice.style.display = 'block';
            
            // Auto-hide after 5 seconds
            setTimeout(() => notice.style.display = 'none', 5000);
        }
    });

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
            
            // Only fit bounds if user hasn't been located AND markers are primarily in NYC
            if (!userLocated && data.points.length > 0) {
                const b = markers.getBounds();
                const nycBounds = L.latLngBounds([40.4774, -74.2591], [40.9176, -73.7004]);
                
                // Only fit bounds if most markers are within NYC bounds (not just intersecting)
                // Check if the center of all markers is within NYC
                const center = b.getCenter();
                if (nycBounds.contains(center)) {
                    map.fitBounds(b, { padding: [50, 50], maxZoom: 14 });
                }
                // Otherwise, keep the Manhattan view set in initialization
            }
        })
        .catch(error => {
            console.error('Error loading art locations:', error);
            alert('Failed to load art locations. Please refresh the page.');
        });
})();

