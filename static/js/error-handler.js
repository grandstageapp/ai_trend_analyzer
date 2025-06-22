// Enhanced Error Handler - Load before main.js
(function() {
    'use strict';
    
    // Comprehensive error suppression for cross-origin script errors
    let errorsSuppressed = 0;
    
    // Override console.error to filter out Script errors
    const originalConsoleError = console.error;
    console.error = function(...args) {
        // Suppress various patterns of script errors
        if ((args.length >= 2 && args[0] === 'JavaScript Error:' && args[1] === null) ||
            (args.length >= 1 && args[0] === 'Script error.') ||
            (args.length >= 1 && typeof args[0] === 'string' && args[0].includes('Script error'))) {
            errorsSuppressed++;
            return; // Suppress these error patterns
        }
        originalConsoleError.apply(console, args);
    };
    
    // Override window.onerror completely - must be synchronous
    const originalOnError = window.onerror;
    window.onerror = function(message, source, lineno, colno, error) {
        if (message === 'Script error.' || 
            !message || 
            message === '' ||
            message === null ||
            (source === '' && lineno === 0) ||
            (source === null && lineno === 0) ||
            message.includes('Script error')) {
            errorsSuppressed++;
            return true; // Completely suppress this error
        }
        return false; // Allow legitimate errors
    };
    
    // Enhanced global error listener with multiple phases
    window.addEventListener('error', function(event) {
        if (event.message === 'Script error.' || 
            event.message === '' || 
            event.message === null ||
            (event.source === null && event.lineno === 0) ||
            (event.filename === '' && event.lineno === 0) ||
            event.message.includes('Script error')) {
            errorsSuppressed++;
            event.preventDefault();
            event.stopImmediatePropagation();
            event.stopPropagation();
            return false;
        }
    }, true); // Use capture phase
    
    // Also capture in bubble phase
    window.addEventListener('error', function(event) {
        if (event.message === 'Script error.' || 
            event.message === '' || 
            event.message === null ||
            event.message.includes('Script error')) {
            errorsSuppressed++;
            event.preventDefault();
            event.stopImmediatePropagation();
            event.stopPropagation();
            return false;
        }
    }, false);
    
    // Report suppression status
    setTimeout(() => {
        if (errorsSuppressed > 0) {
            console.log(`Enhanced error handler: suppressed ${errorsSuppressed} cross-origin errors`);
        } else {
            console.log('Enhanced error handler: active and monitoring');
        }
    }, 2000);
    
    console.log('Enhanced error handler loaded');
})();