// Initialize Leaflet map
document.addEventListener('DOMContentLoaded', function() {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;

    // Initialize map centered on NYC
    const map = L.map('map').setView([40.7128, -74.0060], 12);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    // Get locations data from page if available
    const locationsData = window.locationsData || [];
    
    locationsData.forEach(location => {
        const marker = L.marker([location.latitude, location.longitude]).addTo(map);
        marker.bindPopup(`
            <strong>${location.name}</strong><br>
            ${location.description ? location.description.substring(0, 100) + '...' : ''}<br>
            <a href="/locations/${location.id}/">View Details</a>
        `);
    });

    // Add user location if available
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const userLat = position.coords.latitude;
            const userLng = position.coords.longitude;
            L.circle([userLat, userLng], {
                color: 'blue',
                fillColor: '#30f',
                fillOpacity: 0.3,
                radius: 500
            }).addTo(map).bindPopup('You are here');
        });
    }
});

