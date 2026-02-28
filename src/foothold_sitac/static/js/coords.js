/* Coords JS - Coordinate formatting functions */

// Get coordinate format preference from localStorage
function getCoordFormat() {
    return localStorage.getItem('foothold-coord-format') || 'dms';
}

// Save coordinate format preference
function saveCoordFormat(format) {
    localStorage.setItem('foothold-coord-format', format);
}

// Convert decimal degrees to DMS (degrees, minutes, seconds)
function decimalToDMS(decimal, isLat) {
    var direction = isLat ? (decimal >= 0 ? 'N' : 'S') : (decimal >= 0 ? 'E' : 'W');
    var absolute = Math.abs(decimal);
    var degrees = Math.floor(absolute);
    var minutesDecimal = (absolute - degrees) * 60;
    var minutes = Math.floor(minutesDecimal);
    var seconds = ((minutesDecimal - minutes) * 60).toFixed(2);
    return degrees + '° ' + minutes + "' " + seconds + '" ' + direction;
}

// Convert decimal degrees to decimal minutes (DDM)
function decimalToDDM(decimal, isLat) {
    var direction = isLat ? (decimal >= 0 ? 'N' : 'S') : (decimal >= 0 ? 'E' : 'W');
    var absolute = Math.abs(decimal);
    var degrees = Math.floor(absolute);
    var minutes = ((absolute - degrees) * 60).toFixed(4);
    return degrees + '° ' + minutes + "' " + direction;
}

// Format coordinate with prefix N/S E/W and fixed width (decimal format)
function formatCoordDecimal(decimal, isLat) {
    var dir = isLat ? (decimal >= 0 ? 'N' : 'S') : (decimal >= 0 ? 'E' : 'W');
    var abs = Math.abs(decimal);
    var degPad = isLat ? 2 : 3;
    return dir + abs.toFixed(6).padStart(degPad + 7, '0') + '°';
}

// Format coordinate in DDM format
function formatCoordDDM(decimal, isLat) {
    var dir = isLat ? (decimal >= 0 ? 'N' : 'S') : (decimal >= 0 ? 'E' : 'W');
    var abs = Math.abs(decimal);
    var degPad = isLat ? 2 : 3;
    var deg = Math.floor(abs);
    var min = ((abs - deg) * 60).toFixed(4);
    return dir + String(deg).padStart(degPad, '0') + '°' + min.padStart(7, '0') + "'";
}

// Format coordinate in DMS format
function formatCoordDMS(decimal, isLat) {
    var dir = isLat ? (decimal >= 0 ? 'N' : 'S') : (decimal >= 0 ? 'E' : 'W');
    var abs = Math.abs(decimal);
    var degPad = isLat ? 2 : 3;
    var deg = Math.floor(abs);
    var minDec = (abs - deg) * 60;
    var min = Math.floor(minDec);
    var sec = ((minDec - min) * 60).toFixed(2);
    return dir + String(deg).padStart(degPad, '0') + '°' + String(min).padStart(2, '0') + "'" + sec.padStart(5, '0') + '"';
}

// Format coordinate based on user preference
function formatCoord(decimal, isLat) {
    var format = getCoordFormat();
    switch(format) {
        case 'decimal':
            return formatCoordDecimal(decimal, isLat);
        case 'ddm':
            return formatCoordDDM(decimal, isLat);
        case 'dms':
        default:
            return formatCoordDMS(decimal, isLat);
    }
}

// Calculate distance between two points using Haversine formula
// Returns distance in meters
function calculateDistance(lat1, lon1, lat2, lon2) {
    var R = 6371000; // Earth's radius in meters
    var dLat = (lat2 - lat1) * Math.PI / 180;
    var dLon = (lon2 - lon1) * Math.PI / 180;
    var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

// Calculate bearing from point 1 to point 2
// Returns bearing in degrees (0-360)
function calculateBearing(lat1, lon1, lat2, lon2) {
    var dLon = (lon2 - lon1) * Math.PI / 180;
    var lat1Rad = lat1 * Math.PI / 180;
    var lat2Rad = lat2 * Math.PI / 180;

    var y = Math.sin(dLon) * Math.cos(lat2Rad);
    var x = Math.cos(lat1Rad) * Math.sin(lat2Rad) -
            Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLon);

    var bearing = Math.atan2(y, x) * 180 / Math.PI;
    return (bearing + 360) % 360; // Normalize to 0-360
}

// Format distance in km and nautical miles
function formatDistance(meters) {
    var km = meters / 1000;
    var nm = meters / 1852; // 1 nautical mile = 1852 meters
    return km.toFixed(1) + ' km / ' + nm.toFixed(1) + ' NM';
}

// Format bearing with cardinal direction
function formatBearing(degrees) {
    var cardinals = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                     'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    var index = Math.round(degrees / 22.5) % 16;
    return degrees.toFixed(0) + '° (' + cardinals[index] + ')';
}

// Calculate flight time given distance (meters) and speed (knots)
function calculateFlightTime(distanceMeters, speedKnots) {
    var distanceNm = distanceMeters / 1852;
    var hours = distanceNm / speedKnots;
    var minutes = Math.round(hours * 60);

    if (minutes < 60) {
        return minutes + ' min';
    } else {
        var hrs = Math.floor(minutes / 60);
        var mins = minutes % 60;
        return hrs + 'h ' + mins + 'min';
    }
}

// Get ruler speed preference from localStorage (default 250 knots)
function getRulerSpeed() {
    var speed = localStorage.getItem('foothold-ruler-speed');
    return speed ? parseInt(speed) : 250;
}

// Save ruler speed preference
function saveRulerSpeed(speed) {
    localStorage.setItem('foothold-ruler-speed', speed);
    // If ruler is active, update the display
    if (typeof updateRulerWidget === 'function') {
        updateRulerWidget();
    }
}

// ============================================
// Coordinate parsing functions (text -> decimal)
// ============================================

// Parse coordinates from various formats
// Returns {lat, lon} or null if parsing fails
function parseCoordinates(text) {
    if (!text) return null;
    // Try each format in order
    return parseDMS(text) || parseDDM(text) || parseDecimal(text);
}

// Parse DMS format: "N 31°35'09" E 64°23'10"" or "N31°35'09.18"E64°23'10.11""
function parseDMS(text) {
    // Match patterns like: N 31°35'09" E 64°23'10" or N31°35'09.18"E64°23'10.11"
    // Supports various quote styles: ', ', ", "
    var regex = /([NS])\s*(\d+)[°]\s*(\d+)[''′]\s*([\d.]+)[""″]?\s*([EW])\s*(\d+)[°]\s*(\d+)[''′]\s*([\d.]+)[""″]?/i;
    var match = text.match(regex);
    if (!match) return null;

    var latDir = match[1].toUpperCase();
    var latDeg = parseFloat(match[2]);
    var latMin = parseFloat(match[3]);
    var latSec = parseFloat(match[4]);

    var lonDir = match[5].toUpperCase();
    var lonDeg = parseFloat(match[6]);
    var lonMin = parseFloat(match[7]);
    var lonSec = parseFloat(match[8]);

    var lat = latDeg + latMin / 60 + latSec / 3600;
    if (latDir === 'S') lat = -lat;

    var lon = lonDeg + lonMin / 60 + lonSec / 3600;
    if (lonDir === 'W') lon = -lon;

    return { lat: lat, lon: lon };
}

// Parse DDM format: "N 31°35.153' E 64°23.168'"
function parseDDM(text) {
    // Match patterns like: N 31°35.153' E 64°23.168' or N31°35.153'E64°23.168'
    // Must have decimal in minutes but NO seconds
    var regex = /([NS])\s*(\d+)[°]\s*(\d+\.\d+)[''′]\s*([EW])\s*(\d+)[°]\s*(\d+\.\d+)[''′]/i;
    var match = text.match(regex);
    if (!match) return null;

    var latDir = match[1].toUpperCase();
    var latDeg = parseFloat(match[2]);
    var latMin = parseFloat(match[3]);

    var lonDir = match[4].toUpperCase();
    var lonDeg = parseFloat(match[5]);
    var lonMin = parseFloat(match[6]);

    var lat = latDeg + latMin / 60;
    if (latDir === 'S') lat = -lat;

    var lon = lonDeg + lonMin / 60;
    if (lonDir === 'W') lon = -lon;

    return { lat: lat, lon: lon };
}

// Parse decimal format: "31.58583, 64.38611" or "31.58583 64.38611"
function parseDecimal(text) {
    // Match patterns like: 31.58583, 64.38611 or 31.58583 64.38611
    // Also supports negative values for S/W
    var regex = /(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)/;
    var match = text.match(regex);
    if (!match) return null;

    var lat = parseFloat(match[1]);
    var lon = parseFloat(match[2]);

    // Basic validation
    if (isNaN(lat) || isNaN(lon)) return null;
    if (lat < -90 || lat > 90) return null;
    if (lon < -180 || lon > 180) return null;

    return { lat: lat, lon: lon };
}

// ============================================
// Coordinate formatting functions (decimal -> text)
// ============================================

// Format coordinates for cursor widget with fixed width based on format preference
function formatCursorCoords(lat, lng) {
    var format = getCoordFormat();
    var latDir = lat >= 0 ? 'N' : 'S';
    var lngDir = lng >= 0 ? 'E' : 'W';
    var absLat = Math.abs(lat);
    var absLng = Math.abs(lng);

    if (format === 'decimal') {
        var latStr = latDir + ' ' + absLat.toFixed(6).padStart(10, '0') + '°';
        var lngStr = lngDir + ' ' + absLng.toFixed(6).padStart(11, '0') + '°';
        return latStr + ' ' + lngStr;
    }

    var latDeg = Math.floor(absLat);
    var latMinDec = (absLat - latDeg) * 60;
    var lngDeg = Math.floor(absLng);
    var lngMinDec = (absLng - lngDeg) * 60;

    if (format === 'ddm') {
        var latMin = latMinDec.toFixed(4);
        var lngMin = lngMinDec.toFixed(4);
        var latStr = latDir + String(latDeg).padStart(2, '0') + '°' + latMin.padStart(7, '0') + "'";
        var lngStr = lngDir + String(lngDeg).padStart(3, '0') + '°' + lngMin.padStart(7, '0') + "'";
        return latStr + ' ' + lngStr;
    }

    // DMS format
    var latMin = Math.floor(latMinDec);
    var latSec = ((latMinDec - latMin) * 60).toFixed(2);
    var lngMin = Math.floor(lngMinDec);
    var lngSec = ((lngMinDec - lngMin) * 60).toFixed(2);

    var latStr = latDir + String(latDeg).padStart(2, '0') + '°' + String(latMin).padStart(2, '0') + "'" + latSec.padStart(5, '0') + '"';
    var lngStr = lngDir + String(lngDeg).padStart(3, '0') + '°' + String(lngMin).padStart(2, '0') + "'" + lngSec.padStart(5, '0') + '"';
    return latStr + ' ' + lngStr;
}
