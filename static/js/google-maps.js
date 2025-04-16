// Google Maps Integration for HIRE Platform

// Global variables
let map;
let marker;
let geocoder;
let autocomplete;

// Initialize the Google Maps functionality
function initGoogleMaps() {
    // Initialize the map
    initMap();
    
    // Initialize the autocomplete
    initAutocomplete();
}

// Initialize the map
function initMap() {
    // Default center coordinates (Ireland)
    const defaultCenter = { lat: 53.1424, lng: -7.6921 };
    
    // Create the map instance
    map = new google.maps.Map(document.getElementById('map-container'), {
        center: defaultCenter,
        zoom: 7,
        mapTypeControl: true,
        streetViewControl: false,
        fullscreenControl: true,
        zoomControl: true,
        styles: [
            {
                "featureType": "all",
                "elementType": "geometry",
                "stylers": [
                    {
                        "color": "#242f3e"
                    }
                ]
            },
            {
                "featureType": "all",
                "elementType": "labels.text.fill",
                "stylers": [
                    {
                        "color": "#746855"
                    }
                ]
            },
            {
                "featureType": "all",
                "elementType": "labels.text.stroke",
                "stylers": [
                    {
                        "color": "#242f3e"
                    },
                    {
                        "lightness": 10
                    }
                ]
            },
            {
                "featureType": "administrative.locality",
                "elementType": "labels.text.fill",
                "stylers": [
                    {
                        "color": "#d59563"
                    }
                ]
            },
            {
                "featureType": "poi",
                "elementType": "labels.text.fill",
                "stylers": [
                    {
                        "color": "#d59563"
                    }
                ]
            },
            {
                "featureType": "poi.park",
                "elementType": "geometry",
                "stylers": [
                    {
                        "color": "#263c3f"
                    }
                ]
            },
            {
                "featureType": "poi.park",
                "elementType": "labels.text.fill",
                "stylers": [
                    {
                        "color": "#6b9a76"
                    }
                ]
            },
            {
                "featureType": "road",
                "elementType": "geometry",
                "stylers": [
                    {
                        "color": "#38414e"
                    }
                ]
            },
            {
                "featureType": "road",
                "elementType": "geometry.stroke",
                "stylers": [
                    {
                        "color": "#212a37"
                    }
                ]
            },
            {
                "featureType": "road",
                "elementType": "labels.text.fill",
                "stylers": [
                    {
                        "color": "#9ca5b3"
                    }
                ]
            },
            {
                "featureType": "road.highway",
                "elementType": "geometry",
                "stylers": [
                    {
                        "color": "#746855"
                    }
                ]
            },
            {
                "featureType": "road.highway",
                "elementType": "geometry.stroke",
                "stylers": [
                    {
                        "color": "#1f2835"
                    }
                ]
            },
            {
                "featureType": "road.highway",
                "elementType": "labels.text.fill",
                "stylers": [
                    {
                        "color": "#f3d19c"
                    }
                ]
            },
            {
                "featureType": "transit",
                "elementType": "geometry",
                "stylers": [
                    {
                        "color": "#2f3948"
                    }
                ]
            },
            {
                "featureType": "transit.station",
                "elementType": "labels.text.fill",
                "stylers": [
                    {
                        "color": "#d59563"
                    }
                ]
            },
            {
                "featureType": "water",
                "elementType": "geometry",
                "stylers": [
                    {
                        "color": "#17263c"
                    }
                ]
            },
            {
                "featureType": "water",
                "elementType": "labels.text.fill",
                "stylers": [
                    {
                        "color": "#515c6d"
                    }
                ]
            },
            {
                "featureType": "water",
                "elementType": "labels.text.stroke",
                "stylers": [
                    {
                        "lightness": -20
                    }
                ]
            }
        ]
    });
    
    // Initialize the geocoder
    geocoder = new google.maps.Geocoder();
    
    // Add click event listener to the map
    map.addListener('click', function(event) {
        placeMarker(event.latLng);
        geocodeLatLng(event.latLng);
    });
}

// Initialize the autocomplete functionality
function initAutocomplete() {
    // Get the input element
    const input = document.getElementById('address_search');
    
    // Create the autocomplete instance
    autocomplete = new google.maps.places.Autocomplete(input, {
        types: ['geocode']
    });
    
    // Add place_changed event listener
    autocomplete.addListener('place_changed', function() {
        const place = autocomplete.getPlace();
        
        if (!place.geometry) {
            // User entered the name of a place that was not suggested
            window.alert("No details available for input: '" + place.name + "'");
            return;
        }
        
        // If the place has a geometry, then present it on a map
        if (place.geometry.viewport) {
            map.fitBounds(place.geometry.viewport);
        } else {
            map.setCenter(place.geometry.location);
            map.setZoom(17);
        }
        
        // Place a marker at the location
        placeMarker(place.geometry.location);
        
        // Fill in the address fields
        fillInAddress(place);
    });
}

// Place a marker on the map
function placeMarker(location) {
    // Clear existing marker
    if (marker) {
        marker.setMap(null);
    }
    
    // Create new marker
    marker = new google.maps.Marker({
        position: location,
        map: map,
        animation: google.maps.Animation.DROP
    });
    
    // Pan to the marker
    map.panTo(location);
    
    // Store the coordinates in hidden fields
    document.getElementById('latitude').value = location.lat();
    document.getElementById('longitude').value = location.lng();
}

// Geocode a latitude/longitude to an address
function geocodeLatLng(latLng) {
    geocoder.geocode({ 'location': latLng }, function(results, status) {
        if (status === 'OK') {
            if (results[0]) {
                // Fill in the address fields
                fillInAddress(results[0]);
                
                // Update the search input
                document.getElementById('address_search').value = results[0].formatted_address;
            } else {
                window.alert('No results found');
            }
        } else {
            window.alert('Geocoder failed due to: ' + status);
        }
    });
}

// Fill in the address fields from a place object
function fillInAddress(place) {
    // Get the address components
    const addressComponents = place.address_components;
    
    // Clear the address fields
    document.getElementById('address_line').value = '';
    document.getElementById('city').value = '';
    document.getElementById('state').value = '';
    document.getElementById('postal_code').value = '';
    
    // Fill in the address fields
    document.getElementById('address_line').value = place.formatted_address.split(',')[0];
    
    // Fill in other address components
    for (const component of addressComponents) {
        const componentType = component.types[0];
        
        switch (componentType) {
            case 'street_number':
                // Already handled in address_line
                break;
            case 'route':
                // Already handled in address_line
                break;
            case 'locality':
            case 'postal_town':
                document.getElementById('city').value = component.long_name;
                break;
            case 'administrative_area_level_1':
                document.getElementById('state').value = component.long_name;
                break;
            case 'postal_code':
                document.getElementById('postal_code').value = component.long_name;
                break;
        }
    }
}

// Helper function to get address component
function getAddressComponent(components, type) {
    const component = components.find(comp => comp.types.includes(type));
    return component ? component.long_name : null;
}

// Get current location using browser's geolocation API
function getCurrentLocation() {
    console.log('getCurrentLocation called');
    if (navigator.geolocation) {
        // Show loading indicator or message
        const locateBtn = document.getElementById('locate-me-btn');
        const originalBtnText = locateBtn.innerHTML;
        locateBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Locating...';
        locateBtn.disabled = true;
        locateBtn.classList.add('locating');
        
        // Create a toast notification
        showNotification('Locating your position...', 'info');
        
        console.log('Requesting geolocation...');
        navigator.geolocation.getCurrentPosition(
            function(position) {
                // Success callback
                console.log('Geolocation success:', position.coords);
                const currentLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                
                // Place marker at current location
                placeMarker(currentLocation);
                
                // Center map on current location
                map.setCenter(currentLocation);
                map.setZoom(17);
                
                // Reverse geocode to get address
                geocodeLatLng(currentLocation);
                
                // Reset button
                locateBtn.innerHTML = originalBtnText;
                locateBtn.disabled = false;
                locateBtn.classList.remove('locating');
                
                // Show success notification
                showNotification('Location found successfully!', 'success');
            },
            function(error) {
                // Error callback
                console.error('Geolocation error:', error);
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
                
                // Show error notification instead of alert
                showNotification(errorMessage, 'error');
                
                // Reset button
                locateBtn.innerHTML = originalBtnText;
                locateBtn.disabled = false;
                locateBtn.classList.remove('locating');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    } else {
        console.error('Geolocation not supported');
        showNotification('Geolocation is not supported by this browser.', 'error');
    }
}

// Helper function to show notifications
function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} notification`;
    notification.innerHTML = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '250px';
    notification.style.padding = '15px';
    notification.style.borderRadius = 'var(--border-radius)';
    notification.style.boxShadow = 'var(--box-shadow)';
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s ease';
    
    // Add to body
    document.body.appendChild(notification);
    
    // Fade in
    setTimeout(() => {
        notification.style.opacity = '1';
    }, 10);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

// Initialize when the window loads
window.initGoogleMaps = initGoogleMaps;