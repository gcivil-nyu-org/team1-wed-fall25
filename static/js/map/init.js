/**
 * Map Initialization Orchestrator
 * Main entry point for map functionality - coordinates all modules
 */

import { MAP_CONFIG } from './config.js';
import { createTileLayers, addLayerControl } from './layers.js';
import { GeolocationManager } from './geolocation.js';
import { MarkerManager } from './markers.js';
import { EventMarkerManager } from './events.js';

/**
 * Initialize and setup the Artinerary map
 * @returns {Promise<Object>} Object containing map instance and managers
 */
export async function initializeMap() {
    try {
        // 1. Create map with Manhattan default view
        const map = L.map('map').setView(
            MAP_CONFIG.defaultCenter,
            MAP_CONFIG.defaultZoom
        );

        // 2. Setup tile layers and layer control
        const tileLayers = createTileLayers();
        addLayerControl(map, tileLayers);

        // 3. Initialize geolocation manager
        const geoManager = new GeolocationManager(map);

        // 4. Initialize marker manager
        const markerManager = new MarkerManager(map, geoManager);

        // 5. Initialize event marker manager
        const eventMarkerManager = new EventMarkerManager(map);

        // 6. Request user location (async, non-blocking)
        geoManager.requestLocation();

        // 7. Load art markers (async)
        await markerManager.loadMarkers();

        // 8. Load event markers (async)
        await eventMarkerManager.loadEventMarkers();

        // console.log('Map initialized successfully');

        // Return instances for potential external use
        return {
            map,
            geoManager,
            markerManager,
            eventMarkerManager
        };

    } catch (error) {
        console.error('Failed to initialize map:', error);
        throw error;
    }
}

// Export for global access if needed
window.ArtineraryMap = { initializeMap };

