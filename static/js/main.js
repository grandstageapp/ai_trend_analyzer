// AI Trends Analyzer - Main JavaScript

// Additional error suppression layer
window.addEventListener('error', function(event) {
    // Suppress any remaining script errors that got through
    if (event.message === 'Script error.' || 
        event.message === '' || 
        event.message === null ||
        event.message?.includes('Script error')) {
        console.log('Main.js: Suppressed cross-origin script error (backup layer)');
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
        return false;
    }
    
    // Log legitimate errors for debugging but don't show to user unless critical
    if (event.error && event.error.stack && !event.message?.includes('Script error')) {
        console.warn('Legitimate JavaScript Error:', event.error);
    }
    
    return false;
});

// Global promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.warn('Unhandled promise rejection:', event.reason);
    // Don't show user-facing errors for network/resource loading issues
    if (event.reason && (
        event.reason.message?.includes('fetch') ||
        event.reason.message?.includes('network') ||
        event.reason.message?.includes('load')
    )) {
        event.preventDefault();
    }
});

// Global application state
const AITrendsApp = {
    config: {
        refreshInterval: 300000, // 5 minutes
        animationDuration: 300,
        chartColors: {
            primary: '#0d6efd',
            success: '#198754',
            warning: '#ffc107',
            danger: '#dc3545',
            info: '#0dcaf0'
        }
    },
    
    state: {
        isAutoRefreshEnabled: true,
        lastUpdateTime: Date.now(),
        activeFilters: {},
        searchDebounceTimer: null
    }
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    console.log('Initializing AI Trends Analyzer...');
    
    try {
        // Initialize components with error boundaries
        safeInitialize('Navigation', initializeNavigation);
        safeInitialize('Search', initializeSearch);
        safeInitialize('Filters', initializeFilters);
        safeInitialize('Trend Cards', initializeTrendCards);
        safeInitialize('Tooltips', initializeTooltips);
        safeInitialize('Auto Refresh', initializeAutoRefresh);
        safeInitialize('Keyboard Shortcuts', initializeKeyboardShortcuts);
        safeInitialize('Expandable Description', initializeExpandableDescription);
        safeInitialize('HTMX Events', initializeHTMXEvents);
        
        console.log('AI Trends Analyzer initialized successfully');
    } catch (error) {
        console.error('Critical error initializing application:', error);
        // Only show error for truly critical failures
        if (isCriticalError(error)) {
            showError('Application initialization failed. Please refresh the page.');
        }
    }
}

function safeInitialize(componentName, initFunction) {
    try {
        initFunction();
    } catch (error) {
        console.warn(`Non-critical error initializing ${componentName}:`, error);
        // Continue with other components
    }
}

function isCriticalError(error) {
    // Only consider errors critical if they prevent core functionality
    const criticalKeywords = ['database', 'authentication', 'authorization', 'csrf'];
    return criticalKeywords.some(keyword => 
        error.message?.toLowerCase().includes(keyword)
    );
}

// Navigation Management
function initializeNavigation() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    // Add scroll effect to navbar
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
}

// Search Functionality
function initializeSearch() {
    const searchInput = document.getElementById('search');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        // Clear previous debounce timer
        if (AITrendsApp.state.searchDebounceTimer) {
            clearTimeout(AITrendsApp.state.searchDebounceTimer);
        }
        
        // Set new debounce timer
        AITrendsApp.state.searchDebounceTimer = setTimeout(() => {
            performSearch(query);
        }, 500);
    });
    
    // Handle search form submission
    const searchForm = document.getElementById('filterForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(searchForm);
            const params = new URLSearchParams(formData);
            
            // Update URL and reload
            const newUrl = `${window.location.pathname}?${params.toString()}`;
            window.history.pushState({}, '', newUrl);
            location.reload();
        });
    }
}

function performSearch(query) {
    if (!query) {
        // If empty query, reload all trends
        const trendsContainer = document.getElementById('trendsContainer');
        if (trendsContainer && window.location.pathname === '/') {
            location.reload();
        }
        return;
    }
    
    // Update UI to show searching state
    showSearchingState();
    
    // HTMX will handle the actual search request
    console.log(`Searching for: ${query}`);
}

function showSearchingState() {
    const searchSpinner = document.getElementById('searchSpinner');
    if (searchSpinner) {
        searchSpinner.style.display = 'block';
    }
}

// Filter Management
function initializeFilters() {
    const filterSelects = document.querySelectorAll('#date_filter, #sort');
    
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            // Add loading state
            showLoadingOverlay();
            
            // Small delay to show loading state
            setTimeout(() => {
                select.closest('form').submit();
            }, 100);
        });
    });
}

// Trend Cards Management
function initializeTrendCards() {
    animateTrendCards();
    initializeTrendCardEvents();
}

function animateTrendCards() {
    const cards = document.querySelectorAll('.trend-card');
    
    cards.forEach((card, index) => {
        // Set initial state
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        
        // Animate in with staggered delay
        setTimeout(() => {
            card.style.transition = 'all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

function initializeTrendCardEvents() {
    const cards = document.querySelectorAll('.trend-card');
    
    cards.forEach(card => {
        // Add click tracking
        card.addEventListener('click', function(e) {
            // Only track if not clicking on a button or link
            if (!e.target.closest('a, button')) {
                const trendTitle = card.querySelector('.card-title a')?.textContent;
                console.log(`Trend card clicked: ${trendTitle}`);
            }
        });
        
        // Add hover effects
        card.addEventListener('mouseenter', function() {
            card.style.zIndex = '10';
        });
        
        card.addEventListener('mouseleave', function() {
            card.style.zIndex = '1';
        });
    });
}

// Tooltip Management
function initializeTooltips() {
    // Check if Bootstrap is available
    if (typeof bootstrap === 'undefined') {
        console.warn('Bootstrap not loaded, skipping tooltip initialization');
        return;
    }
    
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover focus'
        });
    });
    
    console.log(`Initialized ${tooltipList.length} tooltips`);
}

// Auto Refresh Management (Disabled to prevent errors)
function initializeAutoRefresh() {
    // Auto-refresh disabled to prevent page reload errors
    console.log('Auto-refresh disabled for stability');
    
    // Still track visibility changes for logging
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            console.log('Auto-refresh paused (tab not visible)');
        } else {
            console.log('Auto-refresh resumed');
        }
    });
}

function shouldAutoRefresh() {
    const timeSinceLastUpdate = Date.now() - AITrendsApp.state.lastUpdateTime;
    return timeSinceLastUpdate > AITrendsApp.config.refreshInterval;
}

function performAutoRefresh() {
    // Auto-refresh disabled - manual refresh only
    console.log('Auto-refresh disabled - use manual refresh if needed');
    AITrendsApp.state.lastUpdateTime = Date.now();
}

function showSubtleRefreshIndicator() {
    // Create or show a subtle refresh indicator
    let indicator = document.getElementById('refreshIndicator');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'refreshIndicator';
        indicator.className = 'position-fixed top-0 start-50 translate-middle-x bg-primary text-white px-3 py-1 rounded-bottom';
        indicator.style.zIndex = '1050';
        indicator.innerHTML = '<small><i class="material-icons me-1" style="font-size: 14px;">refresh</i>Updating trends...</small>';
        document.body.appendChild(indicator);
    }
    
    indicator.style.display = 'block';
    
    // Hide after a few seconds
    setTimeout(() => {
        indicator.style.display = 'none';
    }, 3000);
}

// Keyboard Shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search focus
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('search');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Escape to clear search
        if (e.key === 'Escape') {
            const searchInput = document.getElementById('search');
            if (searchInput && searchInput === document.activeElement) {
                searchInput.value = '';
                searchInput.blur();
                // Trigger search clear
                performSearch('');
            }
        }
        
        // R for refresh (when not in input)
        if (e.key === 'r' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            location.reload();
        }
    });
}

// HTMX Event Handlers
function initializeHTMXEvents() {
    // Before HTMX request
    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        console.log('HTMX request starting...');
        showLoadingOverlay();
    });
    
    // After HTMX request
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        console.log('HTMX request completed');
        hideLoadingOverlay();
        
        // Re-initialize components for new content
        setTimeout(() => {
            initializeTrendCards();
            initializeTooltips();
        }, 100);
    });
    
    // HTMX error handling
    document.body.addEventListener('htmx:responseError', function(evt) {
        console.log('HTMX request failed (non-critical):', evt.detail);
        hideLoadingOverlay();
        // Only show user errors for critical HTMX failures (auth, server errors)
        if (evt.detail.xhr?.status >= 500) {
            showError('Server error occurred. Please try again.');
        }
    });
    
    // HTMX timeout handling
    document.body.addEventListener('htmx:timeout', function(evt) {
        console.warn('HTMX request timed out');
        hideLoadingOverlay();
        showError('Request timed out. Please check your connection and try again.');
    });
}

// Loading Overlay Management
function showLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('d-none');
    }
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('d-none');
    }
}

// Notification Management
function showSuccess(message) {
    try {
        const toast = document.getElementById('successToast');
        const toastBody = document.getElementById('successToastBody');
        
        if (toast && toastBody && typeof bootstrap !== 'undefined') {
            toastBody.textContent = message;
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        } else {
            console.log('Success:', message);
        }
    } catch (error) {
        console.error('Error showing success toast:', error);
        console.log('Success:', message);
    }
}

function showError(message) {
    // Don't show errors for script/resource loading issues
    if (message?.includes('Script error') || 
        message?.includes('failed to load') ||
        message?.includes('network') ||
        message?.includes('fetch')) {
        console.log('Suppressed non-actionable error:', message);
        return;
    }
    
    try {
        const toast = document.getElementById('errorToast');
        const toastBody = document.getElementById('errorToastBody');
        
        if (toast && toastBody && typeof bootstrap !== 'undefined') {
            toastBody.textContent = message;
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        } else {
            console.error('Error:', message);
            // Only show alert for critical errors
            if (isCriticalUserError(message)) {
                alert('Error: ' + message);
            }
        }
    } catch (error) {
        console.error('Error showing error toast:', error);
        if (isCriticalUserError(message)) {
            console.error('Critical Error:', message);
            alert('Error: ' + message);
        }
    }
}

function isCriticalUserError(message) {
    const criticalKeywords = ['authentication', 'authorization', 'payment', 'database', 'server'];
    return criticalKeywords.some(keyword => 
        message?.toLowerCase().includes(keyword)
    );
}

function showInfo(title, message) {
    // Create and show info toast
    const toastHtml = `
        <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-info text-white">
                <i class="material-icons me-2">info</i>
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        </div>
    `;
    
    const toastContainer = document.querySelector('.toast-container');
    if (toastContainer) {
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const newToast = toastContainer.lastElementChild;
        const bsToast = new bootstrap.Toast(newToast);
        bsToast.show();
        
        // Remove toast element after it's hidden
        newToast.addEventListener('hidden.bs.toast', function() {
            newToast.remove();
        });
    }
}

// About Modal
function showAbout() {
    const modal = new bootstrap.Modal(document.getElementById('aboutModal'));
    modal.show();
}

// Utility Functions
function formatNumber(num) {
    if (num < 1000) return num.toString();
    if (num < 1000000) return (num / 1000).toFixed(1) + 'K';
    return (num / 1000000).toFixed(1) + 'M';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays} days ago`;
    
    return date.toLocaleDateString();
}

// Expandable Description Toggle
function initializeExpandableDescription() {
    const toggleButton = document.getElementById('toggleButton');
    const toggleIcon = document.getElementById('toggleIcon');
    const toggleText = document.getElementById('toggleText');
    const fullDescription = document.getElementById('fullDescription');
    
    if (toggleButton && fullDescription) {
        fullDescription.addEventListener('shown.bs.collapse', function() {
            if (toggleIcon) toggleIcon.textContent = 'expand_less';
            if (toggleText) toggleText.textContent = 'Read less';
        });
        
        fullDescription.addEventListener('hidden.bs.collapse', function() {
            if (toggleIcon) toggleIcon.textContent = 'expand_more';
            if (toggleText) toggleText.textContent = 'Read more';
        });
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Error Handling
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
    showError('An unexpected error occurred. Please refresh the page.');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled Promise Rejection:', e.reason);
    showError('A network error occurred. Please check your connection.');
});

// Expose global functions
window.AITrendsApp = AITrendsApp;
window.showSuccess = showSuccess;
window.showError = showError;
window.showInfo = showInfo;
window.showAbout = showAbout;
window.formatNumber = formatNumber;
window.formatDate = formatDate;

console.log('AI Trends Analyzer main.js loaded successfully');
