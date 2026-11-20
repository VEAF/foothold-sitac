/* I18N JS - Translated texts of the map page */

// The texts in the page's language, set by the page from the server (foothold_sitac/i18n.py, keys "js.*")
var I18N = {};

// The text of a key, with its {name} placeholders filled from params; the key itself when unknown
function t(key, params) {
    var text = Object.prototype.hasOwnProperty.call(I18N, key) ? I18N[key] : key;
    if (!params) return text;
    return text.replace(/\{(\w+)\}/g, function(match, name) {
        return Object.prototype.hasOwnProperty.call(params, name) ? String(params[name]) : match;
    });
}

// The text of an optional key (a side, a zone kind...), or the raw value when there is none
function tOr(key, fallback) {
    return Object.prototype.hasOwnProperty.call(I18N, key) ? I18N[key] : fallback;
}

if (typeof module !== 'undefined') {
    module.exports = {
        t: t,
        tOr: tOr,
        setMessages: function(messages) { I18N = messages; }
    };
}
