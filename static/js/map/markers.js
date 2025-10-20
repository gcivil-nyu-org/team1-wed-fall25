/**
 * Marker Management
 * Handles loading, clustering, and displaying art markers on the map
 */

import { MAP_CONFIG } from './config.js';
import { createPopupContent } from './ui.js';

export class MarkerManager {
    constructor(map, geoManager) {
        this.map = map;
        this.geoManager = geoManager;
        this.markers = null;
        this._initializeClusterGroup();
    }

    /**
     * Initialize marker cluster group
     */
    _initializeClusterGroup() {
        this.markers = L.markerClusterGroup(MAP_CONFIG.clusterOptions);
    }

    /**
     * Load art markers from API and add to map
     */
    async loadMarkers() {
        try {
            const response = await fetch(MAP_CONFIG.api.points);
            const data = await response.json();

            // console.log(`Loaded ${data.points.length} art locations`);

            // Create markers for each art point
            data.points.forEach(point => {
                const marker = L.marker([point.y, point.x]);
                const popupContent = createPopupContent(point);
                marker.bindPopup(popupContent);
                this.markers.addLayer(marker);
            });

            // Add marker cluster to map
            this.map.addLayer(this.markers);

            // Fit bounds if appropriate
            this._fitBoundsIfNeeded(data.points.length);

        } catch (error) {
            console.error('Error loading art locations:', error);
            alert('Failed to load art locations. Please refresh the page.');
        }
    }

    /**
     * Fit map bounds to markers if user location not set and markers are in NYC
     * @param {number} pointCount - Number of art points loaded
     */
    _fitBoundsIfNeeded(pointCount) {
        // Only fit bounds if user hasn't been located AND there are markers
        if (!this.geoManager.isUserLocated() && pointCount > 0) {
            const b = this.markers.getBounds();
            const nycBounds = L.latLngBounds(
                MAP_CONFIG.nycBounds.southwest,
                MAP_CONFIG.nycBounds.northeast
            );

            // Only fit bounds if most markers are within NYC bounds
            // Check if the center of all markers is within NYC
            const center = b.getCenter();
            if (nycBounds.contains(center)) {
                this.map.fitBounds(b, {
                    padding: [50, 50],
                    maxZoom: MAP_CONFIG.userLocationZoom
                });
            }
            // Otherwise, keep the Manhattan view set in initialization
        }
    }

    /**
     * Get the marker cluster group
     */
    getMarkers() {
        return this.markers;
    }
}

