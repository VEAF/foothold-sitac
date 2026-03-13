/* Tooltips JS - Click support for mobile devices */

function initTooltips(container) {
    var root = container || document;
    var selector = '[data-tooltip]';

    root.querySelectorAll(selector).forEach(function(el) {
        el.addEventListener('click', function(e) {
            var wasActive = el.classList.contains('tooltip-active');
            // Close all tooltips first
            root.querySelectorAll('.tooltip-active').forEach(function(other) {
                other.classList.remove('tooltip-active');
            });
            // Toggle clicked tooltip
            if (!wasActive) {
                el.classList.add('tooltip-active');
            }
        });
    });

    // Close tooltips when clicking elsewhere
    document.addEventListener('click', function(e) {
        if (!e.target.closest(selector)) {
            root.querySelectorAll('.tooltip-active').forEach(function(el) {
                el.classList.remove('tooltip-active');
            });
        }
    });
}

// Auto-init for standalone pages
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() { initTooltips(); });
} else {
    initTooltips();
}
