/* Modals JS - Modal management functions */

// Modal endpoints (to be set by the page)
var modalEndpoints = {};

// Open modal and load content
function openModal(type) {
    var overlay = document.getElementById('modal-overlay');
    var body = document.getElementById('modal-body');

    body.innerHTML = '<div class="modal-loading">Loading...</div>';
    overlay.classList.add('visible');

    fetch(modalEndpoints[type])
        .then(function(response) {
            if (!response.ok) throw new Error('Failed to load');
            return response.text();
        })
        .then(function(html) {
            body.innerHTML = html;

            // Execute scripts that were injected via innerHTML
            body.querySelectorAll('script').forEach(function(oldScript) {
                var newScript = document.createElement('script');
                newScript.textContent = oldScript.textContent;
                oldScript.parentNode.replaceChild(newScript, oldScript);
            });
        })
        .catch(function(error) {
            body.innerHTML = '<div class="modal-loading">Error loading data</div>';
        });
}

// Close modal
function closeModal() {
    document.getElementById('modal-overlay').classList.remove('visible', 'zone-modal');
}

// Close modal when clicking on overlay
function closeModalOnOverlay(event) {
    if (event.target === document.getElementById('modal-overlay')) {
        closeModal();
    }
}

// Open settings modal
function openSettingsModal() {
    var overlay = document.getElementById('modal-overlay');
    var body = document.getElementById('modal-body');
    var currentFormat = localStorage.getItem('foothold-coord-format') || 'dms';

    body.innerHTML =
        '<h2 style="margin-top: 0;"><i class="fa-solid fa-gear"></i> Settings</h2>' +
        '<div class="settings-section">' +
            '<label>Coordinate format</label>' +
            '<select id="coord-format-select" onchange="saveCoordFormat(this.value)">' +
                '<option value="dms"' + (currentFormat === 'dms' ? ' selected' : '') + '>DMS (N41°07\'24.42")</option>' +
                '<option value="ddm"' + (currentFormat === 'ddm' ? ' selected' : '') + '>DDM (N41°07.4070\')</option>' +
                '<option value="decimal"' + (currentFormat === 'decimal' ? ' selected' : '') + '>Decimal (41.123456°)</option>' +
            '</select>' +
        '</div>';
    overlay.classList.add('visible', 'zone-modal');
}

// Open pilot modal with coordinates in all formats
function openPilotModal(pilot) {
    var overlay = document.getElementById('modal-overlay');
    var body = document.getElementById('modal-body');

    var color = pilot.lost_credits > 0 ? '#28a745' : '#e67e22';

    body.innerHTML =
        '<div class="pilot-modal-header">' +
            '<i class="fa-solid fa-parachute-box" style="color: ' + color + ';"></i>' +
            '<h2>' + pilot.player_name + '</h2>' +
        '</div>' +
        '<div class="pilot-coords">' +
            '<h3>Decimal Degrees</h3>' +
            '<div class="pilot-coords-row">' +
                '<span class="pilot-coords-label">Latitude</span>' +
                '<span class="pilot-coords-value">' + formatCoordDecimal(pilot.lat, true) + '</span>' +
            '</div>' +
            '<div class="pilot-coords-row">' +
                '<span class="pilot-coords-label">Longitude</span>' +
                '<span class="pilot-coords-value">' + formatCoordDecimal(pilot.lon, false) + '</span>' +
            '</div>' +
        '</div>' +
        '<div class="pilot-coords">' +
            '<h3>Degrees Decimal Minutes (DDM)</h3>' +
            '<div class="pilot-coords-row">' +
                '<span class="pilot-coords-label">Latitude</span>' +
                '<span class="pilot-coords-value">' + formatCoordDDM(pilot.lat, true) + '</span>' +
            '</div>' +
            '<div class="pilot-coords-row">' +
                '<span class="pilot-coords-label">Longitude</span>' +
                '<span class="pilot-coords-value">' + formatCoordDDM(pilot.lon, false) + '</span>' +
            '</div>' +
        '</div>' +
        '<div class="pilot-coords">' +
            '<h3>Degrees Minutes Seconds (DMS)</h3>' +
            '<div class="pilot-coords-row">' +
                '<span class="pilot-coords-label">Latitude</span>' +
                '<span class="pilot-coords-value">' + formatCoordDMS(pilot.lat, true) + '</span>' +
            '</div>' +
            '<div class="pilot-coords-row">' +
                '<span class="pilot-coords-label">Longitude</span>' +
                '<span class="pilot-coords-value">' + formatCoordDMS(pilot.lon, false) + '</span>' +
            '</div>' +
        '</div>' +
        '<div class="pilot-coords">' +
            '<h3>Other Info</h3>' +
            '<div class="pilot-coords-row">' +
                '<span class="pilot-coords-label">Altitude</span>' +
                '<span class="pilot-coords-value">' + Math.round(pilot.altitude) + 'm</span>' +
            '</div>' +
            '<div class="pilot-coords-row">' +
                '<span class="pilot-coords-label">Lost Credits</span>' +
                '<span class="pilot-coords-value">' + Math.round(pilot.lost_credits) + '</span>' +
            '</div>' +
        '</div>';
    overlay.classList.add('visible');
}

// Tab switching function
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(function(el) {
        el.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(function(el) {
        el.classList.remove('active');
    });

    // Show selected tab
    document.getElementById('tab-' + tabName).classList.add('active');
    document.querySelector('.tab-btn.' + tabName).classList.add('active');
}

// Close modal on Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});
