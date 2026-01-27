/* Briefing Editor JavaScript */

// Global state
var briefingMap = null;
var zonesLayer = null;
var objectiveMarkers = {};
var homeplateMarker = null;
var saveTimeout = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initBriefingMap();

    if (IS_EDIT_MODE) {
        setupAutoSave();
        populateZoneSelector();
    }
});

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

    // Draw homeplate if exists
    if (BRIEFING_DATA.homeplate) {
        drawHomeplateMarker(BRIEFING_DATA.homeplate);
    }

    // Right-click to set homeplate in edit mode
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
    if (homeplateMarker) {
        briefingMap.removeLayer(homeplateMarker);
    }

    var icon = L.divIcon({
        className: 'homeplate-marker',
        html: '<i class="fa-solid fa-house"></i>',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });

    homeplateMarker = L.marker([homeplate.latitude, homeplate.longitude], { icon: icon });
    homeplateMarker.bindTooltip(homeplate.name, {
        permanent: true,
        direction: 'bottom',
        className: 'homeplate-label-tooltip'
    });
    homeplateMarker.addTo(briefingMap);
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

    // Homeplate fields
    var homeplateInputs = document.querySelectorAll('#homeplate-name, #homeplate-tacan, #homeplate-runway, #homeplate-frequencies');
    homeplateInputs.forEach(function(el) {
        el.addEventListener('input', scheduleHomeplateSave);
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

var homeplateSaveTimeout = null;

function scheduleHomeplateSave() {
    if (homeplateSaveTimeout) clearTimeout(homeplateSaveTimeout);
    homeplateSaveTimeout = setTimeout(saveHomeplate, 800);
    showSaving();
}

function saveHomeplate() {
    var name = document.getElementById('homeplate-name');
    if (!name || !name.value) return;

    var freqStr = document.getElementById('homeplate-frequencies').value;
    var frequencies = freqStr ? freqStr.split(',').map(function(f) { return f.trim(); }).filter(Boolean) : [];

    var data = {
        name: name.value,
        latitude: BRIEFING_DATA.homeplate ? BRIEFING_DATA.homeplate.latitude : 0,
        longitude: BRIEFING_DATA.homeplate ? BRIEFING_DATA.homeplate.longitude : 0,
        tacan: document.getElementById('homeplate-tacan').value || null,
        runway_heading: parseInt(document.getElementById('homeplate-runway').value) || null,
        frequencies: frequencies
    };

    apiCall('PUT', '/homeplate', data).then(function(hp) {
        BRIEFING_DATA.homeplate = hp;
        showSaved();
    }).catch(function() {
        showSaveError();
    });
}

function openHomeplateModal() {
    document.getElementById('homeplate-modal').classList.add('visible');
}

function openHomeplateModalWithCoords(lat, lon) {
    document.getElementById('new-homeplate-lat').value = lat.toFixed(6);
    document.getElementById('new-homeplate-lon').value = lon.toFixed(6);
    openHomeplateModal();
}

function closeHomeplateModal() {
    document.getElementById('homeplate-modal').classList.remove('visible');
    document.getElementById('homeplate-form').reset();
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

    apiCall('PUT', '/homeplate', data).then(function(hp) {
        BRIEFING_DATA.homeplate = hp;
        drawHomeplateMarker(hp);
        renderHomeplateCard(hp);
        closeHomeplateModal();
        showSaved();
    });
}

function renderHomeplateCard(hp) {
    var container = document.getElementById('homeplate-container');
    container.innerHTML = '<div class="homeplate-card editable" id="homeplate-card">' +
        '<div class="homeplate-header">' +
        '<input type="text" id="homeplate-name" value="' + hp.name + '" class="homeplate-name-input" placeholder="Base name">' +
        '<button onclick="removeHomeplate()" class="btn-remove"><i class="fa-solid fa-trash"></i></button>' +
        '</div>' +
        '<div class="homeplate-fields">' +
        '<div class="field-row"><label>TACAN</label><input type="text" id="homeplate-tacan" value="' + (hp.tacan || '') + '" placeholder="e.g., 21X ICK"></div>' +
        '<div class="field-row"><label>Runway</label><input type="number" id="homeplate-runway" value="' + (hp.runway_heading || '') + '" placeholder="Heading °"></div>' +
        '<div class="field-row"><label>Frequencies</label><input type="text" id="homeplate-frequencies" value="' + (hp.frequencies || []).join(', ') + '" placeholder="e.g., 251.0 Tower, 360.0 ATIS"></div>' +
        '</div></div>';

    // Re-attach auto-save listeners
    var inputs = container.querySelectorAll('input');
    inputs.forEach(function(el) {
        el.addEventListener('input', scheduleHomeplateSave);
    });
}

function removeHomeplate() {
    if (!confirm('Remove homeplate?')) return;

    apiCall('DELETE', '/homeplate').then(function() {
        BRIEFING_DATA.homeplate = null;
        if (homeplateMarker) {
            briefingMap.removeLayer(homeplateMarker);
            homeplateMarker = null;
        }
        document.getElementById('homeplate-container').innerHTML =
            '<div class="empty-section"><p>No homeplate defined. Right-click on the map or click <i class="fa-solid fa-plus"></i> to add.</p></div>';
        showSaved();
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
        '<table class="flights-table"><thead><tr><th>Callsign</th><th>Aircraft</th><th>#</th><th>Mission</th><th>PUSH</th><th>TOT</th><th></th></tr></thead>' +
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

    var html = '<tr id="flight-' + flight.id + '" data-id="' + flight.id + '">' +
        '<td><input type="text" value="' + flight.callsign + '" class="flight-input callsign-input" onchange="updateFlight(\'' + packageId + '\', \'' + flight.id + '\', \'callsign\', this.value)"></td>' +
        '<td><input type="text" value="' + flight.aircraft_type + '" class="flight-input aircraft-input" onchange="updateFlight(\'' + packageId + '\', \'' + flight.id + '\', \'aircraft_type\', this.value)"></td>' +
        '<td><input type="number" min="1" max="8" value="' + flight.num_aircraft + '" class="flight-input num-input" onchange="updateFlight(\'' + packageId + '\', \'' + flight.id + '\', \'num_aircraft\', parseInt(this.value))"></td>' +
        '<td><select class="flight-input mission-select" onchange="updateFlight(\'' + packageId + '\', \'' + flight.id + '\', \'mission_type\', this.value)">' + missionOptions + '</select></td>' +
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

    apiCall('DELETE', '').then(function() {
        window.location.href = '/foothold/briefing';
    });
}
