/* Map JS - Leaflet map initialization and zone/player management */

// Global variables (to be set by the page)
var map_center = null;
var map_options = null;
var map = null;

// Layer groups
var connectionsLayer = null;
var zonesLayer = null;
var playersLayer = null;
var labelsLayer = null;
var ejectionsLayer = null;

// Data arrays
var zonesData = [];
var connectionsData = [];
var playersData = [];
var ejectionsData = [];

// Freshness widget state
var REFRESH_INTERVAL = 30;
var nextRefresh = REFRESH_INTERVAL;
var dataAgeSeconds = 0;
var isConnected = true;

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

    // Update labels, players and ejections on zoom change
    map.on('zoomend', function() {
        updateLabels();
        updatePlayers();
        updateEjections();
    });

    // Cursor position display
    var cursorCoordsEl = document.getElementById('cursor-coords');
    map.on('mousemove', function(e) {
        cursorCoordsEl.textContent = formatCursorCoords(e.latlng.lat, e.latlng.lng);
    });
    map.on('mouseout', function() {
        cursorCoordsEl.textContent = '';
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

    body.innerHTML =
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
                '<td style="padding: 8px 0; color: #8892a0;">Lat / Lon</td>' +
                '<td style="padding: 8px 0; text-align: right; color: #e8eaed;">' + zone.lat.toFixed(6) + ', ' + zone.lon.toFixed(6) + '</td>' +
            '</tr>' +
            '<tr>' +
                '<td style="padding: 8px 0; color: #8892a0;">' + formatLabel + '</td>' +
                '<td style="padding: 8px 0; text-align: right; color: #e8eaed;">' + formattedLat + '<br>' + formattedLon + '</td>' +
            '</tr>' +
        '</table>';
    overlay.classList.add('visible', 'zone-modal');
}

// Zone label functions
function getShortName(name) {
    if (!name || name.length <= 5) return name || '';
    return name.substring(0, 5) + '.';
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
        var label = zone.flavor_text || '';
        if (truckIcon) {
            label += label ? '<br>' + truckIcon : truckIcon;
        }
        return label;
    } else if (zoom <= 10) {
        // medium zoom: short name + flavor_text + truck
        var label = getShortName(zone.name);
        if (zone.flavor_text) {
            label += '<br><span style="font-size: 10px; opacity: 0.8;">' + zone.flavor_text + '</span>';
        }
        if (truckIcon) {
            label += '<br>' + truckIcon;
        }
        return label;
    } else {
        // high zoom: full name + flavor_text + truck with count
        var label = zone.name || '';
        if (zone.flavor_text) {
            label += '<br><span style="font-size: 10px; opacity: 0.8;">' + zone.flavor_text + '</span>';
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
            marker.on('click', function() {
                openZoneModal(zone);
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

        marker.on('click', function() {
            openPilotModal(pilot);
        });

        marker.addTo(ejectionsLayer);
    });
}

function updateNavbar(progress, missionsCount, ejectedPilotsCount) {
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
}

function updateFreshnessWidget() {
    var widget = document.getElementById('freshness-widget');
    var icon = document.getElementById('freshness-icon');
    var countdown = document.getElementById('countdown');
    var tooltip = document.getElementById('freshness-tooltip');

    widget.classList.remove('fresh', 'stale', 'disconnected');

    if (!isConnected) {
        widget.classList.add('disconnected');
        icon.textContent = '⚠️';
        countdown.textContent = 'Offline';
        tooltip.textContent = 'Connection to server lost';
    } else if (dataAgeSeconds < 90) {
        widget.classList.add('fresh');
        icon.textContent = '🕐';
        countdown.textContent = nextRefresh + 's';
        tooltip.textContent = 'Data up to date (' + Math.round(dataAgeSeconds) + 's) • Refresh in ' + nextRefresh + 's';
    } else {
        widget.classList.add('stale');
        icon.textContent = '🕐';
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
            updateNavbar(data.progress, data.missions_count, data.ejected_pilots_count);

            zonesLayer.clearLayers();
            data.zones.forEach(function(p) {
                var circle = L.circle([p.lat, p.lon], {
                    color: p.color,
                    fillColor: p.color,
                    fillOpacity: 0.3,
                    radius: Math.min(20000, Math.max(2000, 2000 * p.level)),
                }).addTo(zonesLayer);

                circle.on('click', function() {
                    openZoneModal(p);
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
