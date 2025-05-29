// static/map.js
// Initialize map and display ocean drift prediction and animated current overlay with error handling

function initMap(origLat = -34.2, origLon = 18.4, driftLat = null, driftLon = null, intervalPositions = null) {
    try {
        // Create the Leaflet map centered on original coordinates
        const map = L.map('map').setView([origLat, origLon], 7);
        window.map = map; // Expose map globally for enhancements

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: 'Leaflet | © OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(map);

        // Mark last known location
        const originMarker = L.marker([origLat, origLon], {
            icon: L.divIcon({
                className: 'custom-marker start-marker',
                html: '<i class="fas fa-map-marker-alt"></i>',
                iconSize: [30, 30],
                iconAnchor: [15, 30]
            })
        }).addTo(map).bindPopup('Incident Location');
        originMarker.openPopup();

        // Create pathPoints array for the drift path
        let pathPoints = [[origLat, origLon]];

        // Add interval markers if available
        if (intervalPositions && intervalPositions.length > 0) {
            // Add intermediate points to the path
            intervalPositions.forEach((position, index) => {
                // Add point to path
                pathPoints.push([position.lat, position.lon]);

                // Add marker at intervals (every other point to avoid clutter)
                if (index % 2 === 0 || intervalPositions.length < 10) {
                    const markerLabel = `+${position.hours}h`;

                    const marker = L.marker([position.lat, position.lon], {
                        icon: L.divIcon({
                            className: 'interval-marker',
                            html: `<div class="marker-dot">${markerLabel}</div>`,
                            iconSize: [36, 20],
                            iconAnchor: [18, 10]
                        })
                    }).addTo(map);

                    const time = new Date(position.timestamp).toLocaleTimeString();
                    const date = new Date(position.timestamp).toLocaleDateString();

                    marker.bindPopup(`
                        <strong>Intermediate Position</strong><br>
                        Time: ${time} ${date}<br>
                        Hours elapsed: ${position.hours}<br>
                        Location: ${position.lat.toFixed(5)}, ${position.lon.toFixed(5)}
                    `);
                }
            });
        }

        // Add final drift position to path
        if (driftLat !== null && driftLon !== null) {
            pathPoints.push([driftLat, driftLon]);

            // Mark predicted drift location
            const driftMarker = L.marker([driftLat, driftLon], {
                icon: L.divIcon({
                    className: 'custom-marker end-marker',
                    html: '<i class="fas fa-location-arrow"></i>',
                    iconSize: [30, 30],
                    iconAnchor: [15, 30]
                })
            }).addTo(map).bindPopup('Predicted Current Location');
        }

        // Draw the drift path
        L.polyline(pathPoints, {
            color: '#ff3300',
            weight: 3,
            opacity: 0.8,
            lineCap: 'round',
            lineJoin: 'round',
            dashArray: '5, 8'
        }).addTo(map);

        // Fit map to show all markers
        if (pathPoints.length > 1) {
            const bounds = L.latLngBounds(pathPoints);
            map.fitBounds(bounds, { padding: [50, 50] });
        }

        // Load animated ocean current vectors
        fetch('/static/current_vectors.json')
            .then(response => {
                if (!response.ok) throw new Error('Failed to fetch ocean vector data');
                return response.json();
            })
            .then(data => {
                if (!data || !data.data || data.data.length === 0) {
                    console.warn('Vector data is empty or malformed.');
                    return;
                }

                const velocityLayer = L.velocityLayer({
                    displayValues: true,
                    displayOptions: {
                        velocityType: 'Ocean Current',
                        position: 'bottomleft',
                        emptyString: 'No current data',
                        angleConvention: 'bearingCW',
                        speedUnit: 'm/s'
                    },
                    data: data,
                    maxVelocity: 3
                });
                map.addLayer(velocityLayer);
            })
            .catch(err => {
                console.error('[ERROR] Loading current_vectors.json:', err);
            });

    } catch (err) {
        console.error('[ERROR] Initializing map:', err);
    }
}
