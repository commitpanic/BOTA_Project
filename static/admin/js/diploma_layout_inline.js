(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Function to handle QR size field visibility
        function updateQRSizeFields() {
            // Find all rows in the inline formset
            $('.diplomas-diplomalayoutelement-content-type-diploma_type .tabular.inline-related tbody tr').each(function() {
                var $row = $(this);
                
                // Skip the add row
                if ($row.hasClass('add-row') || $row.hasClass('empty-form')) {
                    return;
                }
                
                // Get the element_type field value
                var elementType = $row.find('select[name*="element_type"]').val() || 
                                 $row.find('input[name*="element_type"]').val() ||
                                 $row.find('td.field-element_type').text().trim();
                
                // Find the qr_size input field
                var $qrSizeField = $row.find('input[name*="qr_size"]');
                var $qrSizeCell = $qrSizeField.closest('td');
                
                if (elementType !== 'qr_code') {
                    // Not QR code - disable and show N/A
                    $qrSizeField.prop('disabled', true);
                    $qrSizeField.prop('readonly', true);
                    $qrSizeField.val('');
                    $qrSizeField.attr('placeholder', 'N/A');
                    $qrSizeCell.css('background-color', '#f5f5f5');
                } else {
                    // Is QR code - enable field
                    $qrSizeField.prop('disabled', false);
                    $qrSizeField.prop('readonly', false);
                    $qrSizeField.attr('placeholder', '');
                    $qrSizeCell.css('background-color', '');
                    
                    // Set default if empty
                    if (!$qrSizeField.val()) {
                        $qrSizeField.val('3.0');
                    }
                }
            });
        }
        
        // Run on page load
        updateQRSizeFields();
        
        // Run when element_type changes (though it should be readonly)
        $(document).on('change', 'select[name*="element_type"]', function() {
            updateQRSizeFields();
        });
        
        // Run when new inline forms are added
        $(document).on('formset:added', function() {
            setTimeout(updateQRSizeFields, 100);
        });
        
        // Fix checkbox issue - force save of unchecked state
        $('form').on('submit', function() {
            // For unchecked checkboxes, add hidden input with value 'false'
            $('.diplomas-diplomalayoutelement-content-type-diploma_type input[type="checkbox"]').each(function() {
                var $checkbox = $(this);
                if (!$checkbox.is(':checked') && $checkbox.attr('name')) {
                    // Remove any existing hidden field with same name
                    $('input[type="hidden"][name="' + $checkbox.attr('name') + '"]').remove();
                    
                    // Add hidden field with unchecked value
                    $('<input>')
                        .attr('type', 'hidden')
                        .attr('name', $checkbox.attr('name'))
                        .val('false')
                        .insertAfter($checkbox);
                }
            });
        });
    });
})(django.jQuery);
