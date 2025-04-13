// Provider Map Integration for HIRE Platform

// Global variables
let providerMap;
let providerMarkers = [];
let infoWindow;
let serviceAreaCircle;

// Initialize the Provider Map
function initProviderMap() {
    // Default center coordinates (Ireland)
    const defaultCenter = { lat: 53.1424, lng: -7.6921 };
    
    // Create the map instance
    providerMap = new google.maps.Map(document.getElementById('provider-map-container'), {
        center: defaultCenter,
        zoom: 7,
        mapTypeControl: true,
        streetViewControl: false,
        fullscreenControl: true,
        zoomControl: true,
        styles: [] // Use the same styles as in google-maps.js if desired
    });
    
    // Initialize info window for markers
    infoWindow = new google.maps.InfoWindow();
    
    // Load providers if the data is available
    if (typeof providerData !== 'undefined' && providerData.length > 0) {
        loadProviders(providerData);
    }
    
    // Add locate me button if container exists
    const locateMeContainer = document.getElementById('provider-locate-me-container');
    if (locateMeContainer) {
        const locateMeBtn = document.createElement('button');
        locateMeBtn.className = 'btn locate-me-btn';
        locateMeBtn.innerHTML = '<i class="bi bi-geo-alt"></i> Locate Me';
        locateMeBtn.addEventListener('click', locateUserOnProviderMap);
        locateMeContainer.appendChild(locateMeBtn);
    }
}

// Load providers onto the map
function loadProviders(providers) {
    // Clear existing markers
    clearProviderMarkers();
    
    // Add markers for each provider
    providers.forEach(provider => {
        if (provider.latitude && provider.longitude) {
            addProviderMarker(provider);
        }
    });
    
    // Fit bounds to show all markers if there are any
    if (providerMarkers.length > 0) {
        const bounds = new google.maps.LatLngBounds();
        providerMarkers.forEach(marker => {
            bounds.extend(marker.getPosition());
        });
        providerMap.fitBounds(bounds);
    }
}

// Add a marker for a provider
function addProviderMarker(provider) {
    const position = {
        lat: parseFloat(provider.latitude),
        lng: parseFloat(provider.longitude)
    };
    
    // Create marker
    const marker = new google.maps.Marker({
        position: position,
        map: providerMap,
        title: provider.name,
        animation: google.maps.Animation.DROP,
        icon: {
            url: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png' // Blue marker for providers
        }
    });
    
    // Create info window content
    const contentString = `
        <div class="info-window">
            <h5>${provider.name}</h5>
            <p>${provider.address || 'Address not available'}</p>
            <p>Services: ${provider.services || 'Not specified'}</p>
            <p>Rating: ${provider.avg_rating ? `${provider.avg_rating}/5` : 'Not rated yet'}</p>
            <a href="/services/provider/${provider.id}" class="btn btn-sm btn-primary">View Profile</a>
        </div>
    `;
    
    // Add click event to marker
    marker.addListener('click', () => {
        infoWindow.setContent(contentString);
        infoWindow.open(providerMap, marker);
        
        // Show service area if available
        if (provider.service_radius) {
            showServiceArea(position, provider.service_radius, provider.name);
        }
    });
    
    // Add marker to array
    providerMarkers.push(marker);
    
    return marker;
}

// Clear all provider markers from the map
function clearProviderMarkers() {
    providerMarkers.forEach(marker => {
        marker.setMap(null);
    });
    providerMarkers = [];
    
    // Clear service area circle if exists
    if (serviceAreaCircle) {
        serviceAreaCircle.setMap(null);
        serviceAreaCircle = null;
    }
}

// Show service area circle for a provider
function showServiceArea(position, radius, providerName) {
    // Clear existing circle
    if (serviceAreaCircle) {
        serviceAreaCircle.setMap(null);
    }
    
    // Create new circle
    serviceAreaCircle = new google.maps.Circle({
        strokeColor: '#4361ee',
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: '#4361ee',
        fillOpacity: 0.1,
        map: providerMap,
        center: position,
        radius: parseFloat(radius) * 1000, // Convert km to meters
        title: `${providerName}'s Service Area`
    });
}

// Locate user on provider map
function locateUserOnProviderMap() {
    if (navigator.geolocation) {
        // Show loading indicator
        const locateBtn = document.querySelector('#provider-locate-me-container .locate-me-btn');
        if (locateBtn) {
            const originalBtnText = locateBtn.innerHTML;
            locateBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Locating...';
            locateBtn.disabled = true;
            locateBtn.classList.add('locating');
        }
        
        // Show notification
        if (typeof showNotification === 'function') {
            showNotification('Locating your position...', 'info');
        }
        
        navigator.geolocation.getCurrentPosition(
            function(position) {
                // Success callback
                const userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                // Add user marker
                const userMarker = new google.maps.Marker({
                    position: userLocation,
                    map: providerMap,
                    title: 'Your Location',
                    animation: google.maps.Animation.DROP,
                    icon: {
                        url: 'http://maps.google.com/mapfiles/ms/icons/red-dot.png' // Red marker for user
                    }
                });
                
                // Center map on user location
                providerMap.setCenter(userLocation);
                providerMap.setZoom(13);
                
                // Show info window for user location
                infoWindow.setContent('<div><strong>Your Location</strong></div>');
                infoWindow.open(providerMap, userMarker);
                
                // Reset button
                if (locateBtn) {
                    locateBtn.innerHTML = originalBtnText;
                    locateBtn.disabled = false;
                    locateBtn.classList.remove('locating');
                }
                
                // Show success notification
                if (typeof showNotification === 'function') {
                    showNotification('Location found successfully!', 'success');
                }
                
                // Find nearby providers if function exists
                if (typeof findNearbyProviders === 'function') {
                    findNearbyProviders(userLocation);
                }
            },
            function(error) {
                // Error handling similar to getCurrentLocation in google-maps.js
                let errorMessage = 'Unable to retrieve your location. ';
                
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage += 'User denied the request for Geolocation.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage += 'Location information is unavailable.';
                        break;
                    case error.TIMEOUT:
                        errorMessage += 'The request to get user location timed out.';
                        break;
                    case error.UNKNOWN_ERROR:
                        errorMessage += 'An unknown error occurred.';
                        break;
                }
                
                // Show notification
                if (typeof showNotification === 'function') {
                    showNotification(errorMessage, 'error');
                } else {
                    alert(errorMessage);
                }
                
                // Reset button
                if (locateBtn) {
                    locateBtn.innerHTML = originalBtnText;
                    locateBtn.disabled = false;
                    locateBtn.classList.remove('locating');
                }
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    } else {
        const errorMsg = 'Geolocation is not supported by this browser.';
        if (typeof showNotification === 'function') {
            showNotification(errorMsg, 'error');
        } else {
            alert(errorMsg);
        }
    }
}

// Calculate distance between two points
function calculateDistance(point1, point2) {
    const R = 6371; // Radius of the Earth in km
    const dLat = (point2.lat - point1.lat) * Math.PI / 180;
    const dLon = (point2.lng - point1.lng) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(point1.lat * Math.PI / 180) * Math.cos(point2.lat * Math.PI / 180) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distance = R * c; // Distance in km
    return distance;
}

// Find providers near a location
function findNearbyProviders(location, radius = 10) {
    // Filter providers within radius
    const nearbyProviders = [];
    
    if (typeof providerData !== 'undefined' && providerData.length > 0) {
        providerData.forEach(provider => {
            if (provider.latitude && provider.longitude) {
                const providerLocation = {
                    lat: parseFloat(provider.latitude),
                    lng: parseFloat(provider.longitude)
                };
                
                const distance = calculateDistance(location, providerLocation);
                
                if (distance <= radius) {
                    // Add distance to provider object
                    provider.distance = distance.toFixed(1);
                    nearbyProviders.push(provider);
                }
            }
        });
    }
    
    // Sort by distance
    nearbyProviders.sort((a, b) => parseFloat(a.distance) - parseFloat(b.distance));
    
    // Update UI with nearby providers if container exists
    const nearbyProvidersContainer = document.getElementById('nearby-providers-container');
    if (nearbyProvidersContainer) {
        if (nearbyProviders.length > 0) {
            let html = '<h5>Nearby Service Providers</h5><div class="list-group">';
            
            nearbyProviders.forEach(provider => {
                html += `
                    <a href="/services/provider/${provider.id}" class="list-group-item list-group-item-action">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${provider.name}</h6>
                            <small>${provider.distance} km</small>
                        </div>
                        <p class="mb-1">${provider.services || 'Services not specified'}</p>
                        <small>${provider.avg_rating ? `Rating: ${provider.avg_rating}/5` : 'Not rated yet'}</small>
                    </a>
                `;
            });
            
            html += '</div>';
            nearbyProvidersContainer.innerHTML = html;
        } else {
            nearbyProvidersContainer.innerHTML = '<div class="alert alert-info">No service providers found within 10km of your location.</div>';
        }
    }
    
    return nearbyProviders;
}

// Initialize when the window loads
window.initProviderMap = initProviderMap;