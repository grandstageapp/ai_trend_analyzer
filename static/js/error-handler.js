// Enhanced Error Handler - Load before main.js
(function() {
    'use strict';
    
    // Override console.error to filter out Script errors
    const originalConsoleError = console.error;
    console.error = function(...args) {
        // Don't log generic script errors to console
        if (args.length >= 2 && args[0] === 'JavaScript Error:' && args[1] === null) {
            return; // Suppress this specific error pattern
        }
        originalConsoleError.apply(console, args);
    };
    
    // Override window.onerror to prevent Script error popups
    window.onerror = function(message, source, lineno, colno, error) {
        if (message === 'Script error.' || !message) {
            return true; // Prevent default browser error handling
        }
        return false; // Allow other errors to be handled normally
    };
    
    // Enhanced global error listener
    window.addEventListener('error', function(event) {
        if (event.message === 'Script error.' || 
            event.message === '' || 
            (event.source === null && event.lineno === 0)) {
            event.preventDefault();
            event.stopImmediatePropagation();
            return false;
        }
    }, true); // Use capture phase
    
    console.log('Enhanced error handler loaded');
})();