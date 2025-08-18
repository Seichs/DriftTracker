// static/enhancements.js
// Enhancements for DriftTracker app - adds geolocation, clipboard support, and form validation

document.addEventListener('DOMContentLoaded', function() {
    // Initialize current time display
    updatePredictionTime();
    setInterval(updatePredictionTime, 60000); // Update every minute

    // Set up geolocation if the browser supports it
    setupGeolocation();

    // Add copy functionality for coordinates
    setupCopyCoordinates();

    // Form validation
    setupFormValidation();
});

// Update the prediction time display
function updatePredictionTime() {
    const predictionTimeElement = document.getElementById('prediction_time');
    if (predictionTimeElement) {
        const now = new Date();
        predictionTimeElement.value = now.toLocaleTimeString() + " " + now.toLocaleDateString();
    }
}

// Setup geolocation functionality
function setupGeolocation() {
    const geolocateButton = document.createElement('button');
    geolocateButton.type = 'button';
    geolocateButton.innerHTML = '<i class="fas fa-crosshairs"></i> Use My Location';
    geolocateButton.className = 'btn';
    geolocateButton.style.marginTop = '12px';
    geolocateButton.style.marginBottom = '16px';

    // Only add the button if browser supports geolocation
    if (navigator.geolocation) {
        const latitudeInput = document.getElementById('latitude');
        if (latitudeInput) {
            latitudeInput.parentNode.insertBefore(geolocateButton, latitudeInput.nextSibling);

            geolocateButton.addEventListener('click', function() {
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        document.getElementById('latitude').value = position.coords.latitude.toFixed(6);
                        document.getElementById('longitude').value = position.coords.longitude.toFixed(6);

                        if (window.map) {
                            window.map.setView([position.coords.latitude, position.coords.longitude], 10);
                        }
                    },
                    function(error) {
                        let errorMessage = 'Geolocation failed: ';

                        switch(error.code) {
                            case error.PERMISSION_DENIED:
                                errorMessage += 'Location permission denied.';
                                break;
                            case error.POSITION_UNAVAILABLE:
                                errorMessage += 'Location information unavailable.';
                                break;
                            case error.TIMEOUT:
                                errorMessage += 'Location request timed out.';
                                break;
                            default:
                                errorMessage += 'Unknown error occurred.';
                        }

                        alert(errorMessage);
                    },
                    {
                        enableHighAccuracy: true,
                        timeout: 5000,
                        maximumAge: 0
                    }
                );
            });
        }
    }
}

// Setup copy to clipboard functionality for coordinates
function setupCopyCoordinates() {
    // Find only the predicted location result item by looking for the specific icon/text
    const resultItems = document.querySelectorAll('.result-item');
    let predictedLocation = null;

    // Find the specific result item that contains the "Predicted Location" text
    resultItems.forEach(item => {
        const strongElement = item.querySelector('strong');
        if (strongElement && strongElement.textContent.includes('Predicted Location')) {
            predictedLocation = item;
        }
    });

    if (!predictedLocation) return;

    const coordinates = predictedLocation.querySelector('.result-value');
    if (!coordinates) return;

    // Get the coordinate text first
    const coordText = coordinates.textContent.trim();

    // Clear the current content
    coordinates.textContent = '';

    // Create a span for the coordinates text
    const coordSpan = document.createElement('span');
    coordSpan.textContent = coordText;
    coordinates.appendChild(coordSpan);

    // Add a line break for better separation
    coordinates.appendChild(document.createElement('br'));

    // Create a centered container for the button
    const buttonContainer = document.createElement('div');
    buttonContainer.style.textAlign = 'center';
    buttonContainer.style.marginTop = '8px';

    // Create the copy button
    const copyBtn = document.createElement('button');
    copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy Coordinates';
    copyBtn.className = 'copy-btn';
    copyBtn.style.background = 'rgba(59, 130, 246, 0.1)';
    copyBtn.style.border = '1px solid rgba(59, 130, 246, 0.3)';
    copyBtn.style.borderRadius = '4px';
    copyBtn.style.color = 'var(--primary-light)';
    copyBtn.style.cursor = 'pointer';
    copyBtn.style.padding = '4px 12px';
    copyBtn.style.fontSize = '12px';
    copyBtn.title = 'Copy coordinates to clipboard';

    copyBtn.addEventListener('click', function() {
        navigator.clipboard.writeText(coordText).then(
            function() {
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy Coordinates';
                }, 2000);
            },
            function() {
                alert('Failed to copy text');
            }
        );
    });

    // Add button to the centered container
    buttonContainer.appendChild(copyBtn);

    // Add the container to the result value
    coordinates.appendChild(buttonContainer);
}

// Form validation
function setupFormValidation() {
    const form = document.getElementById('drift-form');
    if (!form) return;

    form.addEventListener('submit', function(event) {
        // Validate latitude (-90 to 90)
        const lat = parseFloat(document.getElementById('latitude').value);
        if (isNaN(lat) || lat < -90 || lat > 90) {
            event.preventDefault();
            alert('Latitude must be between -90 and 90 degrees');
            return;
        }

        // Validate longitude (-180 to 180)
        const lon = parseFloat(document.getElementById('longitude').value);
        if (isNaN(lon) || lon < -180 || lon > 180) {
            event.preventDefault();
            alert('Longitude must be between -180 and 180 degrees');
            return;
        }

        // Validate date isn't in the future
        const incidentDate = new Date(
            document.getElementById('date').value + 'T' +
            document.getElementById('time').value
        );

        const now = new Date();
        if (incidentDate > now) {
            event.preventDefault();
            alert('Incident time cannot be in the future');
            return;
        }
    });
}