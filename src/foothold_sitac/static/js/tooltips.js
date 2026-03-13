/* Tooltips JS - Click support for mobile devices (single delegated listener) */

document.addEventListener('click', function(e) {
    var target = e.target.closest('[data-tooltip]');
    if (target) {
        var wasActive = target.classList.contains('tooltip-active');
        // Close all tooltips first
        document.querySelectorAll('.tooltip-active').forEach(function(el) {
            el.classList.remove('tooltip-active');
        });
        // Toggle clicked tooltip
        if (!wasActive) {
            target.classList.add('tooltip-active');
        }
    } else {
        // Clicked outside any tooltip element — close all
        document.querySelectorAll('.tooltip-active').forEach(function(el) {
            el.classList.remove('tooltip-active');
        });
    }
});

// Keep initTooltips as a no-op for backward compatibility with modals.js
function initTooltips() {}
