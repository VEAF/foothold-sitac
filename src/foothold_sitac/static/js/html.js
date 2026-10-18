/* HTML JS - Escaping of data values inserted into HTML strings */

// Escape a value before concatenating it into markup (innerHTML, L.divIcon html, bindTooltip)
function escapeHtml(value) {
    return String(value == null ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

if (typeof module !== 'undefined') {
    module.exports = { escapeHtml: escapeHtml };
}
