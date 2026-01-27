/* Briefing Editor JavaScript */

// Global state
var briefingMap = null;
var zonesLayer = null;
var objectiveMarkers = {};
var homeplateMarkers = {};
var saveTimeout = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initBriefingMap();

    if (IS_EDIT_MODE) {
        setupAutoSave();
        populateZoneSelector();
        populateHomeplateSelects();
        restoreLayoutPreference();

        // Save edit token to localStorage
        saveEditToken(BRIEFING_ID, EDIT_TOKEN);
    }
});

// ============ LocalStorage Functions ============

function saveEditToken(briefingId, token) {
    try {
        var tokens = JSON.parse(localStorage.getItem('briefing_edit_tokens') || '{}');
        tokens[briefingId] = token;
        localStorage.setItem('briefing_edit_tokens', JSON.stringify(tokens));
    } catch (e) {
        console.warn('Could not save edit token to localStorage', e);
    }
}

function getEditToken(briefingId) {
    try {
        var tokens = JSON.parse(localStorage.getItem('briefing_edit_tokens') || '{}');
        return tokens[briefingId] || null;
    } catch (e) {
        return null;
    }
}

function removeEditToken(briefingId) {
    try {
        var tokens = JSON.parse(localStorage.getItem('briefing_edit_tokens') || '{}');
        delete tokens[briefingId];
        localStorage.setItem('briefing_edit_tokens', JSON.stringify(tokens));
    } catch (e) {
        console.warn('Could not remove edit token from localStorage', e);
    }
}

// ============ Layout Toggle Functions ============

function toggleMapPanel() {
    var layout = document.querySelector('.briefing-layout');
    var btn = document.getElementById('toggle-map-btn');
    if (!layout || !btn) return;

    var isExpanded = layout.classList.toggle('expanded');

    // Save preference
    try {
        localStorage.setItem('briefing_editor_expanded', isExpanded ? '1' : '0');
    } catch (e) {}

    // Update button text
    var span = btn.querySelector('span');
    if (span) {
        span.textContent = isExpanded ? 'Show map' : 'Hide map';
    }

    // If showing map again, invalidate size
    if (!isExpanded && briefingMap) {
        setTimeout(function() {
            briefingMap.invalidateSize();
        }, 100);
    }
}

function restoreLayoutPreference() {
    try {
        if (localStorage.getItem('briefing_editor_expanded') === '1') {
            var layout = document.querySelector('.briefing-layout');
            var btn = document.getElementById('toggle-map-btn');
            if (layout && btn) {
                layout.classList.add('expanded');
                var span = btn.querySelector('span');
                if (span) span.textContent = 'Show map';
            }
        }
    } catch (e) {}
}

// ============ Map Functions ============

function initBriefingMap() {
    // Calculate center from zones or use default
    var center = [41, 35];
    var zoneNames = Object.keys(ZONES_DATA);
    if (zoneNames.length > 0) {
        var sumLat = 0, sumLon = 0, count = 0;
        for (var name in ZONES_DATA) {
            var zone = ZONES_DATA[name];
            if (!zone.hidden) {
                sumLat += zone.position.latitude;
                sumLon += zone.position.longitude;
                count++;
            }
        }
        if (count > 0) {
            center = [sumLat / count, sumLon / count];
        }
    }

    briefingMap = L.map('briefing-map').setView(center, 7);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        minZoom: 5,
        maxZoom: 14,
        attribution: 'Tiles &copy; Esri'
    }).addTo(briefingMap);

    zonesLayer = L.layerGroup().addTo(briefingMap);

    // Draw zones
    for (var name in ZONES_DATA) {
        var zone = ZONES_DATA[name];
        if (zone.hidden) continue;

        var color = zone.side === 1 ? '#e53935' : zone.side === 2 ? '#1e88e5' : '#9e9e9e';
        var marker = L.circleMarker([zone.position.latitude, zone.position.longitude], {
            radius: 10,
            color: color,
            fillColor: color,
            fillOpacity: 0.4,
            weight: 2
        });

        // Zone label
        marker.bindTooltip(name, {
            permanent: true,
            direction: 'top',
            className: 'zone-label-tooltip'
        });

        if (IS_EDIT_MODE) {
            marker.zoneName = name;
            marker.on('click', function(e) {
                addObjectiveFromZone(e.target.zoneName);
            });
        }

        marker.addTo(zonesLayer);
    }

    // Draw existing objectives with highlight
    if (BRIEFING_DATA.objectives) {
        BRIEFING_DATA.objectives.forEach(function(obj) {
            highlightObjectiveOnMap(obj.zone_name, obj.id);
        });
    }

    // Draw homeplates
    if (BRIEFING_DATA.homeplates) {
        BRIEFING_DATA.homeplates.forEach(function(hp) {
            drawHomeplateMarker(hp);
        });
    }

    // Right-click to add homeplate in edit mode
    if (IS_EDIT_MODE) {
        briefingMap.on('contextmenu', function(e) {
            openHomeplateModalWithCoords(e.latlng.lat, e.latlng.lng);
        });
    }
}

function highlightObjectiveOnMap(zoneName, objectiveId) {
    var zone = ZONES_DATA[zoneName];
    if (!zone) return;

    if (objectiveMarkers[objectiveId]) {
        briefingMap.removeLayer(objectiveMarkers[objectiveId]);
    }

    var marker = L.circleMarker([zone.position.latitude, zone.position.longitude], {
        radius: 16,
        color: '#ff9800',
        fillColor: '#ff9800',
        fillOpacity: 0.3,
        weight: 3,
        dashArray: '5, 5'
    });
    marker.addTo(briefingMap);
    objectiveMarkers[objectiveId] = marker;
}

function removeObjectiveFromMap(objectiveId) {
    if (objectiveMarkers[objectiveId]) {
        briefingMap.removeLayer(objectiveMarkers[objectiveId]);
        delete objectiveMarkers[objectiveId];
    }
}

function drawHomeplateMarker(homeplate) {
    // Remove existing marker for this homeplate
    if (homeplateMarkers[homeplate.id]) {
        briefingMap.removeLayer(homeplateMarkers[homeplate.id]);
    }

    var icon = L.divIcon({
        className: 'homeplate-marker',
        html: '<i class="fa-solid fa-plane-departure"></i>',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });

    var marker = L.marker([homeplate.latitude, homeplate.longitude], { icon: icon });
    marker.bindTooltip(homeplate.name, {
        permanent: true,
        direction: 'bottom',
        className: 'homeplate-label-tooltip'
    });
    marker.addTo(briefingMap);
    homeplateMarkers[homeplate.id] = marker;
}

function removeHomeplateMarker(homeplateId) {
    if (homeplateMarkers[homeplateId]) {
        briefingMap.removeLayer(homeplateMarkers[homeplateId]);
        delete homeplateMarkers[homeplateId];
    }
}

// ============ API Functions ============

function apiCall(method, endpoint, data) {
    var url = API_BASE + endpoint;
    if (IS_EDIT_MODE) {
        url += (url.indexOf('?') >= 0 ? '&' : '?') + 'token=' + EDIT_TOKEN;
    }
    var options = {
        method: method,
        headers: { 'Content-Type': 'application/json' }
    };
    if (data) {
        options.body = JSON.stringify(data);
    }
    return fetch(url, options).then(function(r) {
        if (!r.ok) throw new Error('API error: ' + r.status);
        if (r.status === 204) return null;
        return r.json();
    });
}

// ============ Auto-save Functions ============

function setupAutoSave() {
    var inputs = document.querySelectorAll('#briefing-title, #mission-date, #mission-time, #situation, #weather, #comms-plan, #notes');
    inputs.forEach(function(el) {
        el.addEventListener('input', scheduleSave);
    });
}

function scheduleSave() {
    if (saveTimeout) clearTimeout(saveTimeout);
    saveTimeout = setTimeout(saveBriefing, 800);
    showSaving();
}

function saveBriefing() {
    var data = {
        title: document.getElementById('briefing-title').value,
        mission_date: document.getElementById('mission-date').value || null,
        mission_time: document.getElementById('mission-time').value || null,
        situation: document.getElementById('situation').value || null,
        weather: document.getElementById('weather').value || null,
        comms_plan: document.getElementById('comms-plan').value || null,
        notes: document.getElementById('notes').value || null
    };

    apiCall('PUT', '', data).then(function() {
        showSaved();
    }).catch(function() {
        showSaveError();
    });
}

function showSaving() {
    var indicator = document.getElementById('save-indicator');
    indicator.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
    indicator.className = 'save-indicator saving';
}

function showSaved() {
    var indicator = document.getElementById('save-indicator');
    indicator.innerHTML = '<i class="fa-solid fa-check"></i> Saved';
    indicator.className = 'save-indicator saved';
}

function showSaveError() {
    var indicator = document.getElementById('save-indicator');
    indicator.innerHTML = '<i class="fa-solid fa-exclamation-triangle"></i> Error';
    indicator.className = 'save-indicator error';
}

// ============ Homeplate Functions ============

var editingHomeplateId = null;

function openHomeplateModal(homeplateId) {
    editingHomeplateId = homeplateId || null;
    var modal = document.getElementById('homeplate-modal');
    var title = document.getElementById('homeplate-modal-title');
    var submitBtn = document.getElementById('homeplate-submit-btn');
    var idField = document.getElementById('edit-homeplate-id');

    if (homeplateId) {
        // Edit mode
        var hp = BRIEFING_DATA.homeplates.find(function(h) { return h.id === homeplateId; });
        if (hp) {
            document.getElementById('new-homeplate-name').value = hp.name;
            document.getElementById('new-homeplate-lat').value = hp.latitude;
            document.getElementById('new-homeplate-lon').value = hp.longitude;
            document.getElementById('new-homeplate-tacan').value = hp.tacan || '';
            document.getElementById('new-homeplate-runway').value = hp.runway_heading || '';
            document.getElementById('new-homeplate-freqs').value = (hp.frequencies || []).join(', ');
            idField.value = homeplateId;
            title.textContent = 'Edit Airbase';
            submitBtn.textContent = 'Update Airbase';
        }
    } else {
        // Add mode
        document.getElementById('homeplate-form').reset();
        idField.value = '';
        title.textContent = 'Add Airbase';
        submitBtn.textContent = 'Add Airbase';
    }

    modal.classList.add('visible');
}

function openHomeplateModalWithCoords(lat, lon) {
    editingHomeplateId = null;
    document.getElementById('homeplate-form').reset();
    document.getElementById('edit-homeplate-id').value = '';
    document.getElementById('new-homeplate-lat').value = lat.toFixed(6);
    document.getElementById('new-homeplate-lon').value = lon.toFixed(6);
    document.getElementById('homeplate-modal-title').textContent = 'Add Airbase';
    document.getElementById('homeplate-submit-btn').textContent = 'Add Airbase';
    document.getElementById('homeplate-modal').classList.add('visible');
}

function closeHomeplateModal() {
    document.getElementById('homeplate-modal').classList.remove('visible');
    document.getElementById('homeplate-form').reset();
    editingHomeplateId = null;
}

function editHomeplate(homeplateId) {
    openHomeplateModal(homeplateId);
}

function submitHomeplate(event) {
    event.preventDefault();

    var freqStr = document.getElementById('new-homeplate-freqs').value;
    var frequencies = freqStr ? freqStr.split(',').map(function(f) { return f.trim(); }).filter(Boolean) : [];

    var data = {
        name: document.getElementById('new-homeplate-name').value,
        latitude: parseFloat(document.getElementById('new-homeplate-lat').value),
        longitude: parseFloat(document.getElementById('new-homeplate-lon').value),
        tacan: document.getElementById('new-homeplate-tacan').value || null,
        runway_heading: parseInt(document.getElementById('new-homeplate-runway').value) || null,
        frequencies: frequencies
    };

    var homeplateId = document.getElementById('edit-homeplate-id').value;

    if (homeplateId) {
        // Update existing
        apiCall('PUT', '/homeplates/' + homeplateId, data).then(function(hp) {
            // Update in local data
            var idx = BRIEFING_DATA.homeplates.findIndex(function(h) { return h.id === homeplateId; });
            if (idx >= 0) {
                BRIEFING_DATA.homeplates[idx] = hp;
            }
            drawHomeplateMarker(hp);
            renderHomeplatesContainer();
            populateHomeplateSelects();
            closeHomeplateModal();
            showSaved();
        });
    } else {
        // Create new
        apiCall('POST', '/homeplates', data).then(function(hp) {
            BRIEFING_DATA.homeplates.push(hp);
            drawHomeplateMarker(hp);
            renderHomeplatesContainer();
            populateHomeplateSelects();
            closeHomeplateModal();
            showSaved();
        });
    }
}

function renderHomeplatesContainer() {
    var container = document.getElementById('homeplates-container');
    if (!container) return;

    if (BRIEFING_DATA.homeplates.length === 0) {
        container.innerHTML = '<div class="empty-section" id="homeplates-empty">' +
            '<p>No airbases defined. Right-click on the map or click <i class="fa-solid fa-plus"></i> to add.</p></div>';
        return;
    }

    var html = '';
    BRIEFING_DATA.homeplates.forEach(function(hp) {
        html += '<div class="homeplate-card editable" data-id="' + hp.id + '">' +
            '<div class="homeplate-header">' +
            '<span class="homeplate-name">' + hp.name + '</span>' +
            '<div class="homeplate-actions">' +
            '<button onclick="editHomeplate(\'' + hp.id + '\')" class="btn-edit"><i class="fa-solid fa-pen"></i></button>' +
            '<button onclick="removeHomeplate(\'' + hp.id + '\')" class="btn-remove"><i class="fa-solid fa-trash"></i></button>' +
            '</div></div>' +
            '<div class="homeplate-info">';

        if (hp.tacan) {
            html += '<span class="info-tag"><i class="fa-solid fa-broadcast-tower"></i> ' + hp.tacan + '</span>';
        }
        if (hp.runway_heading) {
            html += '<span class="info-tag"><i class="fa-solid fa-road"></i> ' + hp.runway_heading + '°</span>';
        }
        if (hp.frequencies && hp.frequencies.length > 0) {
            html += '<span class="info-tag"><i class="fa-solid fa-headset"></i> ' + hp.frequencies.length + ' freq</span>';
        }

        html += '</div></div>';
    });

    container.innerHTML = html;
}

function removeHomeplate(homeplateId) {
    if (!confirm('Remove this airbase?')) return;

    apiCall('DELETE', '/homeplates/' + homeplateId).then(function() {
        BRIEFING_DATA.homeplates = BRIEFING_DATA.homeplates.filter(function(h) { return h.id !== homeplateId; });
        removeHomeplateMarker(homeplateId);
        renderHomeplatesContainer();
        populateHomeplateSelects();
        showSaved();
    });
}

// Populate all homeplate select dropdowns
function populateHomeplateSelects() {
    var selects = document.querySelectorAll('.homeplate-select');
    selects.forEach(function(select) {
        var currentValue = select.value;
        var isDeparture = select.classList.contains('departure-select');
        var defaultOption = isDeparture ? '<option value="">-</option>' : '<option value="">Same</option>';

        var options = defaultOption;
        BRIEFING_DATA.homeplates.forEach(function(hp) {
            options += '<option value="' + hp.id + '">' + hp.name + '</option>';
        });

        select.innerHTML = options;
        select.value = currentValue;
    });

    // Also restore selected values from data attributes
    document.querySelectorAll('tr[data-departure-id]').forEach(function(row) {
        var departureId = row.dataset.departureId;
        var arrivalId = row.dataset.arrivalId;
        var depSelect = row.querySelector('.departure-select');
        var arrSelect = row.querySelector('.arrival-select');
        if (depSelect && departureId) depSelect.value = departureId;
        if (arrSelect && arrivalId) arrSelect.value = arrivalId;
    });
}

// ============ Objective Functions ============

function populateZoneSelector() {
    var list = document.getElementById('zone-selector-list');
    if (!list) return;

    var existingZones = BRIEFING_DATA.objectives.map(function(o) { return o.zone_name; });
    var html = '';

    var sortedZones = Object.keys(ZONES_DATA).filter(function(name) {
        return !ZONES_DATA[name].hidden;
    }).sort();

    sortedZones.forEach(function(name) {
        var zone = ZONES_DATA[name];
        var isAdded = existingZones.indexOf(name) >= 0;
        var sideClass = zone.side === 1 ? 'red' : zone.side === 2 ? 'blue' : 'neutral';

        html += '<div class="zone-selector-item ' + sideClass + (isAdded ? ' added' : '') + '" onclick="' + (isAdded ? '' : 'addObjectiveFromSelector(\'' + name + '\')') + '">' +
            '<span class="zone-name">' + name + '</span>' +
            (isAdded ? '<span class="zone-added"><i class="fa-solid fa-check"></i></span>' : '') +
            '</div>';
    });

    list.innerHTML = html;
}

function openZoneSelectorModal() {
    populateZoneSelector();
    document.getElementById('zone-selector-modal').classList.add('visible');
}

function closeZoneSelectorModal() {
    document.getElementById('zone-selector-modal').classList.remove('visible');
}

function addObjectiveFromZone(zoneName) {
    // Check if already added
    var existing = BRIEFING_DATA.objectives.find(function(o) { return o.zone_name === zoneName; });
    if (existing) return;

    var data = {
        zone_name: zoneName,
        mission_requirements: [],
        priority: BRIEFING_DATA.objectives.length + 1
    };

    apiCall('POST', '/objectives', data).then(function(obj) {
        BRIEFING_DATA.objectives.push(obj);
        appendObjectiveCard(obj);
        highlightObjectiveOnMap(zoneName, obj.id);
        hideEmptySection('objectives');
        showSaved();
    });
}

function addObjectiveFromSelector(zoneName) {
    addObjectiveFromZone(zoneName);
    closeZoneSelectorModal();
}

function appendObjectiveCard(obj) {
    var list = document.getElementById('objectives-list');
    var html = '<div class="objective-card" id="objective-' + obj.id + '" data-id="' + obj.id + '">' +
        '<div class="objective-header">' +
        '<div class="objective-priority-control"><label>P</label>' +
        '<input type="number" min="1" max="9" value="' + obj.priority + '" onchange="updateObjectivePriority(\'' + obj.id + '\', this.value)" class="priority-input"></div>' +
        '<span class="objective-zone">' + obj.zone_name + '</span>' +
        '<button onclick="removeObjective(\'' + obj.id + '\')" class="btn-remove"><i class="fa-solid fa-trash"></i></button>' +
        '</div>' +
        '<div class="mission-badges-editor">';

    MISSION_TYPES.forEach(function(mt) {
        html += '<label class="mission-type-toggle">' +
            '<input type="checkbox" onchange="toggleObjectiveMission(\'' + obj.id + '\', \'' + mt + '\', this.checked)">' +
            '<span class="mission-type-badge ' + mt + '">' + mt + '</span></label>';
    });

    html += '</div><div class="objective-notes-row">' +
        '<input type="text" value="" placeholder="Notes..." onchange="updateObjectiveNotes(\'' + obj.id + '\', this.value)" class="notes-input">' +
        '</div></div>';

    list.insertAdjacentHTML('beforeend', html);
}

function removeObjective(objectiveId) {
    if (!confirm('Remove this objective?')) return;

    apiCall('DELETE', '/objectives/' + objectiveId).then(function() {
        document.getElementById('objective-' + objectiveId).remove();
        removeObjectiveFromMap(objectiveId);
        BRIEFING_DATA.objectives = BRIEFING_DATA.objectives.filter(function(o) { return o.id !== objectiveId; });
        if (BRIEFING_DATA.objectives.length === 0) {
            showEmptySection('objectives');
        }
        showSaved();
    });
}

function updateObjectivePriority(objectiveId, priority) {
    apiCall('PUT', '/objectives/' + objectiveId, { priority: parseInt(priority) }).then(function() {
        var obj = BRIEFING_DATA.objectives.find(function(o) { return o.id === objectiveId; });
        if (obj) obj.priority = parseInt(priority);
        showSaved();
    });
}

function updateObjectiveNotes(objectiveId, notes) {
    apiCall('PUT', '/objectives/' + objectiveId, { notes: notes || null }).then(function() {
        showSaved();
    });
}

function toggleObjectiveMission(objectiveId, missionType, checked) {
    var obj = BRIEFING_DATA.objectives.find(function(o) { return o.id === objectiveId; });
    if (!obj) return;

    var reqs = obj.mission_requirements.map(function(r) { return r.value || r; });
    if (checked && reqs.indexOf(missionType) < 0) {
        reqs.push(missionType);
    } else if (!checked) {
        reqs = reqs.filter(function(r) { return r !== missionType; });
    }

    apiCall('PUT', '/objectives/' + objectiveId, { mission_requirements: reqs }).then(function(updated) {
        obj.mission_requirements = updated.mission_requirements;
        showSaved();
    });
}

// ============ Package Functions ============

function addPackage() {
    var num = BRIEFING_DATA.packages.length + 1;
    var data = {
        name: 'Package ' + String.fromCharCode(64 + num)
    };

    apiCall('POST', '/packages', data).then(function(pkg) {
        BRIEFING_DATA.packages.push(pkg);
        appendPackageCard(pkg);
        hideEmptySection('packages');
        showSaved();
    });
}

function appendPackageCard(pkg) {
    var list = document.getElementById('packages-list');

    var targetOptions = '<option value="">No target</option>';
    BRIEFING_DATA.objectives.forEach(function(obj) {
        targetOptions += '<option value="' + obj.zone_name + '">' + obj.zone_name + '</option>';
    });

    var missionOptions = '<option value="">Mission type</option>';
    MISSION_TYPES.forEach(function(mt) {
        missionOptions += '<option value="' + mt + '">' + mt + '</option>';
    });

    var html = '<div class="package-card" id="package-' + pkg.id + '" data-id="' + pkg.id + '">' +
        '<div class="package-header">' +
        '<input type="text" value="' + pkg.name + '" class="package-name-input" onchange="updatePackageName(\'' + pkg.id + '\', this.value)">' +
        '<select onchange="updatePackageTarget(\'' + pkg.id + '\', this.value)" class="package-target-select">' + targetOptions + '</select>' +
        '<select onchange="updatePackageMission(\'' + pkg.id + '\', this.value)" class="package-mission-select">' + missionOptions + '</select>' +
        '<button onclick="removePackage(\'' + pkg.id + '\')" class="btn-remove"><i class="fa-solid fa-trash"></i></button>' +
        '</div>' +
        '<div class="flights-container">' +
        '<table class="flights-table"><thead><tr><th>Callsign</th><th>Aircraft</th><th>#</th><th>Mission</th><th>Departure</th><th>Arrival</th><th>PUSH</th><th>TOT</th><th></th></tr></thead>' +
        '<tbody id="flights-' + pkg.id + '"></tbody></table>' +
        '<button onclick="addFlight(\'' + pkg.id + '\')" class="btn-add-flight"><i class="fa-solid fa-plus"></i> Add Flight</button>' +
        '</div>' +
        '<div class="package-notes-row">' +
        '<input type="text" value="" placeholder="Package notes..." onchange="updatePackageNotes(\'' + pkg.id + '\', this.value)" class="notes-input">' +
        '</div></div>';

    list.insertAdjacentHTML('beforeend', html);
}

function removePackage(packageId) {
    if (!confirm('Remove this package and all its flights?')) return;

    apiCall('DELETE', '/packages/' + packageId).then(function() {
        document.getElementById('package-' + packageId).remove();
        BRIEFING_DATA.packages = BRIEFING_DATA.packages.filter(function(p) { return p.id !== packageId; });
        if (BRIEFING_DATA.packages.length === 0) {
            showEmptySection('packages');
        }
        showSaved();
    });
}

function updatePackageName(packageId, name) {
    apiCall('PUT', '/packages/' + packageId, { name: name }).then(function() {
        showSaved();
    });
}

function updatePackageTarget(packageId, target) {
    apiCall('PUT', '/packages/' + packageId, { target_zone: target || null }).then(function() {
        showSaved();
    });
}

function updatePackageMission(packageId, missionType) {
    apiCall('PUT', '/packages/' + packageId, { mission_type: missionType || null }).then(function() {
        showSaved();
    });
}

function updatePackageNotes(packageId, notes) {
    apiCall('PUT', '/packages/' + packageId, { notes: notes || null }).then(function() {
        showSaved();
    });
}

// ============ Flight Functions ============

function addFlight(packageId) {
    var data = {
        callsign: 'Flight 1',
        aircraft_type: 'F-16C',
        num_aircraft: 2,
        mission_type: 'CAP'
    };

    apiCall('POST', '/packages/' + packageId + '/flights', data).then(function(flight) {
        var pkg = BRIEFING_DATA.packages.find(function(p) { return p.id === packageId; });
        if (pkg) pkg.flights.push(flight);
        appendFlightRow(packageId, flight);
        showSaved();
    });
}

function appendFlightRow(packageId, flight) {
    var tbody = document.getElementById('flights-' + packageId);

    var missionOptions = '';
    MISSION_TYPES.forEach(function(mt) {
        var sel = (flight.mission_type === mt || (flight.mission_type && flight.mission_type.value === mt)) ? ' selected' : '';
        missionOptions += '<option value="' + mt + '"' + sel + '>' + mt + '</option>';
    });

    var homeplateOptions = '<option value="">-</option>';
    var arrivalOptions = '<option value="">Same</option>';
    BRIEFING_DATA.homeplates.forEach(function(hp) {
        var depSel = flight.departure_id === hp.id ? ' selected' : '';
        var arrSel = flight.arrival_id === hp.id ? ' selected' : '';
        homeplateOptions += '<option value="' + hp.id + '"' + depSel + '>' + hp.name + '</option>';
        arrivalOptions += '<option value="' + hp.id + '"' + arrSel + '>' + hp.name + '</option>';
    });

    var html = '<tr id="flight-' + flight.id + '" data-id="' + flight.id + '" data-departure-id="' + (flight.departure_id || '') + '" data-arrival-id="' + (flight.arrival_id || '') + '">' +
        '<td><input type="text" value="' + flight.callsign + '" class="flight-input callsign-input" onchange="updateFlight(\'' + packageId + '\', \'' + flight.id + '\', \'callsign\', this.value)"></td>' +
        '<td><input type="text" value="' + flight.aircraft_type + '" class="flight-input aircraft-input" onchange="updateFlight(\'' + packageId + '\', \'' + flight.id + '\', \'aircraft_type\', this.value)"></td>' +
        '<td><input type="number" min="1" max="8" value="' + flight.num_aircraft + '" class="flight-input num-input" onchange="updateFlight(\'' + packageId + '\', \'' + flight.id + '\', \'num_aircraft\', parseInt(this.value))"></td>' +
        '<td><select class="flight-input mission-select" onchange="updateFlight(\'' + packageId + '\', \'' + flight.id + '\', \'mission_type\', this.value)">' + missionOptions + '</select></td>' +
        '<td><select class="flight-input homeplate-select departure-select" onchange="updateFlight(\'' + packageId + '\', \'' + flight.id + '\', \'departure_id\', this.value || null)">' + homeplateOptions + '</select></td>' +
        '<td><select class="flight-input homeplate-select arrival-select" onchange="updateFlight(\'' + packageId + '\', \'' + flight.id + '\', \'arrival_id\', this.value || null)">' + arrivalOptions + '</select></td>' +
        '<td><input type="text" value="' + (flight.push_time || '') + '" class="flight-input time-input" placeholder="-" onchange="updateFlight(\'' + packageId + '\', \'' + flight.id + '\', \'push_time\', this.value || null)"></td>' +
        '<td><input type="text" value="' + (flight.tot || '') + '" class="flight-input time-input" placeholder="-" onchange="updateFlight(\'' + packageId + '\', \'' + flight.id + '\', \'tot\', this.value || null)"></td>' +
        '<td><button onclick="removeFlight(\'' + packageId + '\', \'' + flight.id + '\')" class="btn-remove-small"><i class="fa-solid fa-times"></i></button></td>' +
        '</tr>';

    tbody.insertAdjacentHTML('beforeend', html);
}

function removeFlight(packageId, flightId) {
    apiCall('DELETE', '/packages/' + packageId + '/flights/' + flightId).then(function() {
        document.getElementById('flight-' + flightId).remove();
        var pkg = BRIEFING_DATA.packages.find(function(p) { return p.id === packageId; });
        if (pkg) {
            pkg.flights = pkg.flights.filter(function(f) { return f.id !== flightId; });
        }
        showSaved();
    });
}

function updateFlight(packageId, flightId, field, value) {
    var data = {};
    data[field] = value;

    apiCall('PUT', '/packages/' + packageId + '/flights/' + flightId, data).then(function() {
        // Update data attribute if departure/arrival changed
        if (field === 'departure_id' || field === 'arrival_id') {
            var row = document.getElementById('flight-' + flightId);
            if (row) {
                row.dataset[field === 'departure_id' ? 'departureId' : 'arrivalId'] = value || '';
            }
        }
        showSaved();
    });
}

// ============ UI Helper Functions ============

function toggleSection(header) {
    var section = header.closest('.briefing-section');
    section.classList.toggle('collapsed');
}

function hideEmptySection(type) {
    var el = document.getElementById(type + '-empty');
    if (el) el.style.display = 'none';
}

function showEmptySection(type) {
    var el = document.getElementById(type + '-empty');
    if (el) el.style.display = 'block';
}

function openShareModal() {
    document.getElementById('share-modal').classList.add('visible');
}

function closeShareModal() {
    document.getElementById('share-modal').classList.remove('visible');
}

function copyToClipboard(inputId) {
    var input = document.getElementById(inputId);
    input.select();
    input.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(input.value).then(function() {
        var btn = input.nextElementSibling;
        btn.innerHTML = '<i class="fa-solid fa-check"></i>';
        setTimeout(function() {
            btn.innerHTML = '<i class="fa-solid fa-copy"></i>';
        }, 2000);
    });
}

function closeModalOnOverlay(event, modalId) {
    if (event.target.id === modalId) {
        document.getElementById(modalId).classList.remove('visible');
    }
}

function deleteBriefing() {
    if (!confirm('Are you sure you want to delete this briefing? This cannot be undone.')) return;

    // Remove edit token from localStorage
    removeEditToken(BRIEFING_ID);

    apiCall('DELETE', '').then(function() {
        window.location.href = '/foothold/briefing';
    });
}
