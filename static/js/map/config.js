/**
 * Map Configuration and Constants
 * Contains all configuration values and constants used across map modules
 */

export const MAP_CONFIG = {
    // Default map center (Manhattan, NYC)
    defaultCenter: [40.7831, -73.9712],
    
    // Default zoom level
    defaultZoom: 12,
    
    // User location zoom level
    userLocationZoom: 14,
    
    // NYC bounds for validating marker positions
    nycBounds: {
        southwest: [40.4774, -74.2591],
        northeast: [40.9176, -73.7004]
    },
    
    // API endpoints
    api: {
        points: '/loc_detail/api/points/all',
        favoriteToggle: '/loc_detail/api/favorite'
    },
    
    // Marker clustering options
    clusterOptions: {
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true
    },
    
    // User location marker styling
    userMarker: {
        color: '#4285F4',
        fillColor: '#4285F4',
        fillOpacity: 0.1,
        weight: 1
    }
};

