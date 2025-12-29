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
