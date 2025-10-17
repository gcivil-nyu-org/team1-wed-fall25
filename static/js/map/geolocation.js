/**
 * Geolocation Management
 * Handles user location detection, markers, and error handling
 */

import { MAP_CONFIG } from './config.js';

export class GeolocationManager {
    constructor(map) {
        this.map = map;
        this.userLocated = false;
        this.userMarker = null;
        this.userCircle = null;
        
        this._setupEventListeners();
    }
    
    /**
     * Setup event listeners for location found and location error
     */
    _setupEventListeners() {
        this.map.on('locationfound', (e) => this._onLocationFound(e));
        this.map.on('locationerror', (e) => this._onLocationError(e));
    }
    
    /**
     * Request user's current location
     */
    requestLocation() {
        this.map.locate({ 
            setView: true, 
            maxZoom: MAP_CONFIG.userLocationZoom, 
            enableHighAccuracy: true 
        });
    }
    
    /**
     * Handle successful location detection
     */
    _onLocationFound(e) {
        this.userLocated = true;
        const radius = e.accuracy / 2;
        
        // Create blue dot marker (Google Maps style)
        const userIcon = L.divIcon({
            className: 'user-location-marker',
            html: '<div class="user-dot"></div>',
            iconSize: [20, 20]
        });
        
        this.userMarker = L.marker(e.latlng, { icon: userIcon })
            .addTo(this.map)
            .bindPopup("You are here (±" + Math.round(radius) + " meters)")
            .openPopup();
        
        // Add accuracy circle
        this.userCircle = L.circle(e.latlng, radius, {
            color: MAP_CONFIG.userMarker.color,
            fillColor: MAP_CONFIG.userMarker.fillColor,
            fillOpacity: MAP_CONFIG.userMarker.fillOpacity,
            weight: MAP_CONFIG.userMarker.weight
        }).addTo(this.map);

        // Ensure user view wins over any later operations (like fitBounds)
        this.map.setView(e.latlng, MAP_CONFIG.userLocationZoom);
    }
    
    /**
     * Handle location error or denial
     */
    _onLocationError(e) {
        this.userLocated = false;
        console.log('Location access denied or unavailable:', e.message);
        
        // Keep Manhattan default (already set in initialization)
        this._showLocationNotice();
    }
    
    /**
     * Show notice to user about location status
     */
    _showLocationNotice() {
        const notice = document.getElementById('location-notice');
        const noticeText = document.getElementById('notice-text');
        
        if (notice && noticeText) {
            noticeText.textContent = 'Location access not available. Showing NYC area instead.';
            notice.style.display = 'block';
            
            // Auto-hide after 5 seconds
            setTimeout(() => notice.style.display = 'none', 5000);
        }
    }
    
    /**
     * Check if user location has been successfully located
     */
    isUserLocated() {
        return this.userLocated;
    }
}

