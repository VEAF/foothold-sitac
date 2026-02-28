/* Map JS - Leaflet map initialization and zone/player management */

// Global variables (to be set by the page)
var map_center = null;
var map_options = null;
var map = null;

// Server dropdown toggle
function toggleServerDropdown() {
    var dropdown = document.querySelector('.navbar-brand-dropdown');
    dropdown.classList.toggle('open');
}

// Close dropdown when clicking outside
document.addEventListener('click', function(e) {
    var dropdown = document.querySelector('.navbar-brand-dropdown');
    if (dropdown && !dropdown.contains(e.target)) {
        dropdown.classList.remove('open');
    }
});

// Layer groups
var connectionsLayer = null;
var zonesLayer = null;
var playersLayer = null;
var labelsLayer = null;
var ejectionsLayer = null;
var markpointsLayer = null;

// Data arrays
var zonesData = [];
var connectionsData = [];
var playersData = [];
var ejectionsData = [];
var markpointsData = [];

// Freshness widget state (REFRESH_INTERVAL is set by the page from config)
var REFRESH_INTERVAL = 60;
var nextRefresh = REFRESH_INTERVAL;
var dataAgeSeconds = 0;
var isConnected = true;

// Ruler state
var rulerMode = false;
var rulerPoints = [null, null]; // [{lat, lon, name}, {lat, lon, name}]
var rulerLine = null;
var rulerMarkers = [];
var rulerLayer = null;

// API endpoint (to be set by the page)
var mapDataEndpoint = '';

// Initialize the map
function initMap() {
    map = L.map('map').setView(map_center, 8);

    // Base tile layers
    var baseLayers = {};
    var defaultLayer = L.tileLayer(map_options.url_tiles, {
        minZoom: map_options.min_zoom,
        maxZoom: map_options.max_zoom,
        attribution: '&copy; OpenStreetMap'
    });
    baseLayers['Default'] = defaultLayer;
    defaultLayer.addTo(map);

    // Alternative tile layers
    if (map_options.alternative_tiles && map_options.alternative_tiles.length > 0) {
        map_options.alternative_tiles.forEach(function(tile) {
            baseLayers[tile.name] = L.tileLayer(tile.url, {
                minZoom: map_options.min_zoom,
                maxZoom: map_options.max_zoom,
                attribution: '&copy; OpenStreetMap'
            });
        });
        L.control.layers(baseLayers, null, { position: 'topright' }).addTo(map);
    }

    // Initialize layer groups
    connectionsLayer = L.layerGroup().addTo(map);
    zonesLayer = L.layerGroup().addTo(map);
    playersLayer = L.layerGroup().addTo(map);
    labelsLayer = L.layerGroup().addTo(map);
    ejectionsLayer = L.layerGroup().addTo(map);
    markpointsLayer = L.layerGroup().addTo(map);
    rulerLayer = L.layerGroup().addTo(map);

    // Load markpoints from localStorage
    loadMarkpoints();

    // Update labels, players, ejections and markpoints on zoom change
    map.on('zoomend', function() {
        updateLabels();
        updatePlayers();
        updateEjections();
        updateMarkpoints();
    });

    // Cursor position display
    var cursorCoordsEl = document.getElementById('cursor-coords');
    map.on('mousemove', function(e) {
        cursorCoordsEl.textContent = formatCursorCoords(e.latlng.lat, e.latlng.lng);
    });
    map.on('mouseout', function() {
        cursorCoordsEl.textContent = '';
    });

    // Map click for ruler mode
    map.on('click', function(e) {
        if (rulerMode) {
            setRulerPoint(e.latlng.lat, e.latlng.lng, null);
        }
    });
}

// Zone modal
function openZoneModal(zone) {
    var overlay = document.getElementById('modal-overlay');
    var body = document.getElementById('modal-body');

    var format = getCoordFormat();
    var formatLabel = format === 'dms' ? 'DMS' : (format === 'ddm' ? 'DDM' : 'Decimal');
    var formattedLat = formatCoord(zone.lat, true);
    var formattedLon = formatCoord(zone.lon, false);

    var html =
        '<h3 style="margin-top: 0; color: ' + zone.color + ';">' + (zone.name || 'Unknown zone') + '</h3>' +
        '<table style="width: 100%; border-collapse: collapse;">' +
            '<tr>' +
                '<td style="padding: 8px 0; color: #8892a0;">Coalition</td>' +
                '<td style="padding: 8px 0; text-align: right; color: #e8eaed;">' + zone.side + '</td>' +
            '</tr>' +
            '<tr>' +
                '<td style="padding: 8px 0; color: #8892a0;">Detected units</td>' +
                '<td style="padding: 8px 0; text-align: right; color: #e8eaed;">' + zone.units + '</td>' +
            '</tr>' +
            '<tr>' +
                '<td style="padding: 8px 0; color: #8892a0;">Upgrades</td>' +
                '<td style="padding: 8px 0; text-align: right; color: #e8eaed;">' + (zone.upgrades_used || 0) + ' / ' + zone.level + '</td>' +
            '</tr>' +
            '<tr>' +
                '<td style="padding: 8px 0; color: #8892a0;">Lat / Lon</td>' +
                '<td style="padding: 8px 0; text-align: right; color: #e8eaed;">' + zone.lat.toFixed(6) + ', ' + zone.lon.toFixed(6) + '</td>' +
            '</tr>' +
            '<tr>' +
                '<td style="padding: 8px 0; color: #8892a0;">' + formatLabel + '</td>' +
                '<td style="padding: 8px 0; text-align: right; color: #e8eaed;">' + formattedLat + '<br>' + formattedLon + '</td>' +
            '</tr>' +
        '</table>';

    // Add unit groups section if available
    if (zone.unit_groups && zone.unit_groups.length > 0) {
        html += '<div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1);">';
        html += '<h4 style="margin: 0 0 8px 0; color: #8892a0; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Forces</h4>';

        zone.unit_groups.forEach(function(group) {
            var unitList = [];
            for (var unitType in group.units) {
                var count = group.units[unitType];
                unitList.push(unitType + (count > 1 ? ' x' + count : ''));
            }
            html += '<div style="padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">';
            html += '<span style="color: #8892a0; font-size: 12px;">Group ' + group.group_id + '</span><br>';
            html += '<span style="color: #e8eaed; font-size: 13px;">' + unitList.join(', ') + '</span>';
            html += '</div>';
        });

        html += '</div>';
    }

    body.innerHTML = html;
    overlay.classList.add('visible', 'zone-modal');
}

// Zone label functions
function getShortName(name) {
    if (!name || name.length <= 5) return name || '';
    return name.substring(0, 5) + '.';
}

function getFirstLine(text) {
    if (!text) return '';
    var lines = text.split('\n');
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trim();
        if (line) return line;
    }
    return '';
}

function createLabelContent(zone, zoom) {
    var truckIcon = zone.units > 0
        ? '<i class="fa-solid fa-truck" style="color: ' + zone.color + ';"></i>'
        : '';

    if (zoom <= 8) {
        // very low zoom: truck only
        return truckIcon;
    } else if (zoom <= 9) {
        // low zoom: flavor_text only (if available) + truck
        var label = getFirstLine(zone.flavor_text);
        if (truckIcon) {
            label += label ? '<br>' + truckIcon : truckIcon;
        }
        return label;
    } else if (zoom <= 10) {
        // medium zoom: short name + flavor_text + truck
        var label = getShortName(zone.name);
        var flavorLine = getFirstLine(zone.flavor_text);
        if (flavorLine) {
            label += '<br><span style="font-size: 10px; opacity: 0.8;">' + flavorLine + '</span>';
        }
        if (truckIcon) {
            label += '<br>' + truckIcon;
        }
        return label;
    } else {
        // high zoom: full name + flavor_text + truck with count
        var label = zone.name || '';
        var flavorLine = getFirstLine(zone.flavor_text);
        if (flavorLine) {
            label += '<br><span style="font-size: 10px; opacity: 0.8;">' + flavorLine + '</span>';
        }
        if (zone.units > 0) {
            label += '<br>' + truckIcon + ' x' + zone.units;
        }
        return label;
    }
}

function updateLabels() {
    var zoom = map.getZoom();
    labelsLayer.clearLayers();

    zonesData.forEach(function(zone) {
        var content = createLabelContent(zone, zoom);
        if (content) {
            var marker = L.marker([zone.lat, zone.lon], {
                icon: L.divIcon({
                    className: 'zone-label',
                    html: content,
                    iconSize: [100, 40],
                    iconAnchor: [50, 20]
                })
            });
            marker.on('click', function(e) {
                if (rulerMode) {
                    setRulerPoint(zone.lat, zone.lon, zone.name);
                    L.DomEvent.stopPropagation(e);
                } else {
                    openZoneModal(zone);
                }
            });
            marker.addTo(labelsLayer);
        }
    });
}

function updateConnections() {
    connectionsLayer.clearLayers();

    connectionsData.forEach(function(conn) {
        var latlngs = [
            [conn.from_lat, conn.from_lon],
            [conn.to_lat, conn.to_lon]
        ];

        // Draw line
        var line = L.polyline(latlngs, {
            color: conn.color,
            weight: 3,
            opacity: 0.7,
            dashArray: '8, 12'
        });
        line.addTo(connectionsLayer);
    });
}

function createPlayerLabelContent(player, zoom) {
    var planeIcon = '<i class="fa-solid fa-plane" style="color: ' + player.color + ';"></i>';

    if (zoom < 10) {
        // Low zoom: plane icon only
        return planeIcon;
    } else {
        // Zoom 10+: plane icon + player name
        return planeIcon + '<br><span style="font-size: 10px;">' + player.player_name + '</span>';
    }
}

function updatePlayers() {
    var zoom = map.getZoom();
    playersLayer.clearLayers();

    playersData.forEach(function(player) {
        var content = createPlayerLabelContent(player, zoom);
        var marker = L.marker([player.lat, player.lon], {
            icon: L.divIcon({
                className: 'player-label',
                html: content,
                iconSize: [120, 40],
                iconAnchor: [60, 20]
            })
        });
        marker.bindTooltip(player.player_name + '<br>' + player.unit_type, {
            direction: 'top',
            offset: [0, -10]
        });
        marker.on('click', function(e) {
            if (rulerMode) {
                setRulerPoint(player.lat, player.lon, player.player_name);
                L.DomEvent.stopPropagation(e);
            }
        });
        marker.addTo(playersLayer);
    });
}

// Ejected pilots
function updateEjections() {
    var zoom = map.getZoom();
    ejectionsLayer.clearLayers();

    ejectionsData.forEach(function(pilot) {
        var icon = '<i class="fa-solid fa-parachute-box"></i>';
        var content = zoom >= 10
            ? icon + '<br><span style="font-size: 9px;">' + pilot.player_name + '</span>'
            : icon;

        var marker = L.marker([pilot.lat, pilot.lon], {
            icon: L.divIcon({
                className: pilot.lost_credits > 0 ? 'ejection-label green' : 'ejection-label',
                html: content,
                iconSize: [100, 40],
                iconAnchor: [50, 20]
            })
        });

        marker.bindTooltip(pilot.player_name + '<br>Alt: ' + Math.round(pilot.altitude) + 'm', {
            direction: 'top',
            offset: [0, -10]
        });

        marker.on('click', function(e) {
            if (rulerMode) {
                setRulerPoint(pilot.lat, pilot.lon, pilot.player_name);
                L.DomEvent.stopPropagation(e);
            } else {
                openPilotModal(pilot);
            }
        });

        marker.addTo(ejectionsLayer);
    });
}

function updateNavbar(progress, missionsCount, ejectedPilotsCount, blueCredits, redCredits) {
    // Update progress percentage
    var progressElement = document.getElementById('progress-value');
    if (progressElement) {
        progressElement.textContent = Math.round(progress);
    }

    // Update missions count and link state
    var missionsLink = document.getElementById('missions-link');
    var missionsBadge = document.getElementById('missions-badge');
    if (missionsBadge) {
        missionsBadge.textContent = missionsCount;
    }
    if (missionsLink) {
        if (missionsCount === 0) {
            missionsLink.classList.add('disabled');
        } else {
            missionsLink.classList.remove('disabled');
        }
    }

    // Update ejected pilots count and badge style
    var ejectedCount = document.getElementById('ejected-pilots-count');
    if (ejectedCount) {
        ejectedCount.textContent = ejectedPilotsCount;
        if (ejectedPilotsCount > 0) {
            ejectedCount.classList.add('navbar-badge-orange');
            ejectedCount.classList.remove('navbar-badge-gray');
        } else {
            ejectedCount.classList.remove('navbar-badge-orange');
            ejectedCount.classList.add('navbar-badge-gray');
        }
    }

    // Update coalition credits
    var creditsBlue = document.getElementById('credits-blue');
    var creditsRed = document.getElementById('credits-red');
    if (creditsBlue) {
        creditsBlue.textContent = Math.round(blueCredits || 0);
    }
    if (creditsRed) {
        creditsRed.textContent = Math.round(redCredits || 0);
    }
}

function updateFreshnessWidget() {
    var widget = document.getElementById('freshness-widget');
    var countdown = document.getElementById('countdown');
    var tooltip = document.getElementById('freshness-tooltip');
    var progressRing = document.querySelector('.progress-ring-fill');

    widget.classList.remove('fresh', 'stale', 'disconnected');

    // Update progress ring
    if (progressRing) {
        var circumference = 2 * Math.PI * 10; // r=10
        var progressPercent = nextRefresh / REFRESH_INTERVAL;
        var offset = circumference * (1 - progressPercent);
        progressRing.style.strokeDashoffset = offset;
    }

    if (!isConnected) {
        widget.classList.add('disconnected');
        countdown.textContent = 'Offline';
        tooltip.textContent = 'Connection to server lost';
    } else if (dataAgeSeconds < 90) {
        widget.classList.add('fresh');
        countdown.textContent = nextRefresh + 's';
        tooltip.textContent = 'Data up to date (' + Math.round(dataAgeSeconds) + 's) • Refresh in ' + nextRefresh + 's';
    } else {
        widget.classList.add('stale');
        countdown.textContent = nextRefresh + 's';
        var minutes = Math.floor(dataAgeSeconds / 60);
        tooltip.textContent = 'Stale data (' + minutes + 'min) • Refresh in ' + nextRefresh + 's';
    }
}

function loadData() {
    fetch(mapDataEndpoint)
        .then(function(r) {
            if (!r.ok) throw new Error('API error');
            return r.json();
        })
        .then(function(data) {
            isConnected = true;
            dataAgeSeconds = data.age_seconds;
            nextRefresh = REFRESH_INTERVAL;
            updateFreshnessWidget();
            updateNavbar(data.progress, data.missions_count, data.ejected_pilots_count, data.blue_credits, data.red_credits);

            zonesLayer.clearLayers();
            data.zones.forEach(function(p) {
                var circle = L.circle([p.lat, p.lon], {
                    color: p.color,
                    fillColor: p.color,
                    fillOpacity: 0.3,
                    radius: Math.min(20000, Math.max(2000, 2000 * p.level)),
                }).addTo(zonesLayer);

                circle.on('click', function(e) {
                    if (rulerMode) {
                        setRulerPoint(p.lat, p.lon, p.name);
                        L.DomEvent.stopPropagation(e);
                    } else {
                        openZoneModal(p);
                    }
                });
            });

            zonesData = data.zones;
            connectionsData = data.connections || [];
            playersData = data.players || [];
            ejectionsData = data.ejected_pilots || [];
            updateConnections();
            updatePlayers();
            updateEjections();
            updateLabels();
        })
        .catch(function(error) {
            console.error(error);
            isConnected = false;
            updateFreshnessWidget();
        });
}

// Start countdown timer and data refresh
function startRefreshTimer() {
    // Countdown timer - updates every second
    setInterval(function() {
        if (nextRefresh > 0) {
            nextRefresh--;
            dataAgeSeconds++;
        }
        if (nextRefresh <= 0) {
            nextRefresh = REFRESH_INTERVAL;
        }
        updateFreshnessWidget();
    }, 1000);

    // Initial load
    loadData();

    // Refresh every REFRESH_INTERVAL seconds
    setInterval(loadData, REFRESH_INTERVAL * 1000);
}

// Toggle ruler measurement mode
function toggleRulerMode() {
    rulerMode = !rulerMode;
    var toggle = document.getElementById('ruler-toggle');
    var widget = document.getElementById('ruler-widget');

    if (rulerMode) {
        toggle.classList.add('active');
        widget.classList.remove('hidden');
        document.getElementById('map').style.cursor = 'crosshair';
    } else {
        toggle.classList.remove('active');
        widget.classList.add('hidden');
        document.getElementById('map').style.cursor = '';
        clearRuler();
    }
}

// Clear ruler measurement
function clearRuler() {
    rulerPoints = [null, null];
    rulerLayer.clearLayers();
    rulerLine = null;
    rulerMarkers = [];
    updateRulerWidget();
}

// Set a ruler measurement point
function setRulerPoint(lat, lon, name) {
    if (!rulerMode) return;

    // If both points are set, start fresh
    if (rulerPoints[0] && rulerPoints[1]) {
        clearRuler();
    }

    // Determine which point to set
    var pointIndex = rulerPoints[0] ? 1 : 0;
    rulerPoints[pointIndex] = { lat: lat, lon: lon, name: name || null };

    // Create marker for this point
    var markerLabel = pointIndex === 0 ? 'A' : 'B';
    var marker = L.marker([lat, lon], {
        icon: L.divIcon({
            className: 'ruler-marker',
            html: '<div class="ruler-marker-label">' + markerLabel + '</div>',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        })
    }).addTo(rulerLayer);
    rulerMarkers.push(marker);

    // If both points set, draw line
    if (rulerPoints[0] && rulerPoints[1]) {
        drawRulerLine();
    }

    updateRulerWidget();
}

// Draw the ruler line between two points
function drawRulerLine() {
    if (!rulerPoints[0] || !rulerPoints[1]) return;

    if (rulerLine) {
        rulerLayer.removeLayer(rulerLine);
    }

    rulerLine = L.polyline([
        [rulerPoints[0].lat, rulerPoints[0].lon],
        [rulerPoints[1].lat, rulerPoints[1].lon]
    ], {
        color: '#fbbf24',
        weight: 3,
        opacity: 0.9,
        dashArray: '10, 10'
    }).addTo(rulerLayer);
}

// Update the ruler widget display
function updateRulerWidget() {
    var point1Coords = document.getElementById('ruler-point-1');
    var point2Coords = document.getElementById('ruler-point-2');
    var distanceEl = document.getElementById('ruler-distance');
    var bearingEl = document.getElementById('ruler-bearing');
    var timeEl = document.getElementById('ruler-time');

    // Update point displays
    if (rulerPoints[0]) {
        var label1 = rulerPoints[0].name ? rulerPoints[0].name : 'Point A';
        point1Coords.textContent = label1;
    } else {
        point1Coords.textContent = 'Click to set';
    }

    if (rulerPoints[1]) {
        var label2 = rulerPoints[1].name ? rulerPoints[1].name : 'Point B';
        point2Coords.textContent = label2;
    } else {
        point2Coords.textContent = 'Click to set';
    }

    // Calculate and display measurements
    if (rulerPoints[0] && rulerPoints[1]) {
        var distance = calculateDistance(
            rulerPoints[0].lat, rulerPoints[0].lon,
            rulerPoints[1].lat, rulerPoints[1].lon
        );
        var bearing = calculateBearing(
            rulerPoints[0].lat, rulerPoints[0].lon,
            rulerPoints[1].lat, rulerPoints[1].lon
        );
        var speed = getRulerSpeed();

        distanceEl.textContent = formatDistance(distance);
        bearingEl.textContent = formatBearing(bearing);
        timeEl.textContent = calculateFlightTime(distance, speed) + ' @ ' + speed + ' kt';
    } else {
        distanceEl.textContent = '--';
        bearingEl.textContent = '--';
        timeEl.textContent = '--';
    }
}

// ============================================
// Markpoint management functions
// ============================================

// Save markpoints to localStorage
function saveMarkpoints() {
    localStorage.setItem('foothold-markpoints', JSON.stringify(markpointsData));
}

// Load markpoints from localStorage
function loadMarkpoints() {
    var saved = localStorage.getItem('foothold-markpoints');
    if (saved) {
        try {
            markpointsData = JSON.parse(saved);
            updateMarkpoints();
        } catch (e) {
            console.error('Failed to load markpoints:', e);
            markpointsData = [];
        }
    }
}

// Add a new markpoint
function addMarkpoint(lat, lon, label) {
    var markpoint = { lat: lat, lon: lon, label: label || 'Markpoint' };
    markpointsData.push(markpoint);
    saveMarkpoints();
    updateMarkpoints();
}

// Remove a markpoint by index
function removeMarkpoint(index) {
    markpointsData.splice(index, 1);
    saveMarkpoints();
    updateMarkpoints();
}

// Clear all markpoints
function clearAllMarkpoints() {
    markpointsData = [];
    saveMarkpoints();
    updateMarkpoints();
}

// Update markpoints display on map
function updateMarkpoints() {
    markpointsLayer.clearLayers();

    markpointsData.forEach(function(mp, index) {
        var zoom = map.getZoom();
        var content = '<i class="fa-solid fa-location-dot"></i>';
        if (zoom >= 10) {
            content += '<br><span style="font-size: 10px;">' + mp.label + '</span>';
        }

        var marker = L.marker([mp.lat, mp.lon], {
            icon: L.divIcon({
                className: 'markpoint-label',
                html: content,
                iconSize: [100, 40],
                iconAnchor: [50, 20]
            })
        });

        marker.bindTooltip(mp.label + '<br>' + formatCoord(mp.lat, true) + '<br>' + formatCoord(mp.lon, false), {
            direction: 'top',
            offset: [0, -10]
        });

        marker.on('click', function(e) {
            if (rulerMode) {
                setRulerPoint(mp.lat, mp.lon, mp.label);
                L.DomEvent.stopPropagation(e);
            } else {
                openMarkpointDetailModal(mp, index);
            }
        });

        marker.addTo(markpointsLayer);
    });
}
