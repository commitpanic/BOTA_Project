// Simple script - just handle form behavior
(function() {
    'use strict';
    
    // Wait for jQuery
    function waitForJQuery() {
        if (typeof django !== 'undefined' && django.jQuery) {
            setupQRFields(django.jQuery);
        } else if (typeof jQuery !== 'undefined') {
            setupQRFields(jQuery);
        } else {
            setTimeout(waitForJQuery, 50);
        }
    }
    
    function setupQRFields($) {
        $(document).ready(function() {
            // Nothing special needed - let the form work normally
            // Model.save() will handle clearing qr_size for non-QR elements
        });
    }
    
    waitForJQuery();
})();
