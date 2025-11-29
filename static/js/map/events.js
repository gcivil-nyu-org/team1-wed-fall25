/**
 * Event Markers Management
 * Handles loading and displaying event markers on the map
 */

export class EventMarkerManager {
    constructor(map) {
        this.map = map;
        this.eventMarkers = L.layerGroup();
    }

    /**
     * Load event markers from API and add to map
     */
    async loadEventMarkers() {
        try {
            const response = await fetch('/events/api/pins/');
            const data = await response.json();

            console.log(`Loaded ${data.points.length} event locations`);

            // Create markers for each event
            data.points.forEach(event => {
                // Create purple marker for events
                const purpleIcon = L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                });

                const marker = L.marker([event.y, event.x], { icon: purpleIcon });

                // Create popup with event info
                const popupContent = `
                    <div class="event-popup">
                        <h3 style="margin: 0 0 0.5rem 0;">${event.t}</h3>
                        <p style="margin: 0 0 0.5rem 0;"><strong>Event</strong></p>
                        <a href="/events/${event.slug}/" 
                           class="btn btn-primary">
                            View Event
                        </a>
                    </div>
                `;

                marker.bindPopup(popupContent);

                // Add click handler to navigate to event detail
                marker.on('click', () => {
                    // Popup will show with the link
                });

                this.eventMarkers.addLayer(marker);
            });

            // Add event markers layer to map
            this.map.addLayer(this.eventMarkers);

        } catch (error) {
            console.error('Error loading event locations:', error);
        }
    }

    /**
     * Remove all event markers from map
     */
    clearEventMarkers() {
        this.eventMarkers.clearLayers();
    }
}

