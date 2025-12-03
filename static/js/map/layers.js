/**
 * Tile Layer Management
 * Handles creation and management of different map tile layers
 */

/**
 * Creates all available tile layer options
 * @returns {Object} Object containing all tile layer options
 */
export function createTileLayers() {
    return {
        // "Vibrant": L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        //     attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        //     subdomains: 'abcd',
        //     maxZoom: 20
        // }),
        "Streets": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        })
    };
}

/**
 * Adds layer control to the map with the specified tile layers
 * @param {L.Map} map - The Leaflet map instance
 * @param {Object} layers - Object containing tile layers
 */
export function addLayerControl(map, layers) {
    // Add default layer (Vibrant)
    layers["Streets"].addTo(map);

    // Add layer control to allow users to switch between styles
    // L.control.layers(layers).addTo(map);
}

