// AI Trends Analyzer - Main JavaScript

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
        // Initialize components
        initializeNavigation();
        initializeSearch();
        initializeFilters();
        initializeTrendCards();
        initializeTooltips();
        initializeAutoRefresh();
        initializeKeyboardShortcuts();
        initializeExpandableDescription();
        
        // Initialize HTMX event listeners
        initializeHTMXEvents();
        
        console.log('AI Trends Analyzer initialized successfully');
    } catch (error) {
        console.error('Error initializing application:', error);
        // Show error to user
        showError('Application initialization failed. Please refresh the page.');
    }
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

// Auto Refresh Management
function initializeAutoRefresh() {
    if (!AITrendsApp.state.isAutoRefreshEnabled) return;
    
    setInterval(() => {
        if (!document.hidden && shouldAutoRefresh()) {
            performAutoRefresh();
        }
    }, AITrendsApp.config.refreshInterval);
    
    // Pause auto-refresh when tab is not visible
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            console.log('Auto-refresh paused (tab not visible)');
        } else {
            console.log('Auto-refresh resumed');
            // Check if we need to refresh after becoming visible
            if (shouldAutoRefresh()) {
                performAutoRefresh();
            }
        }
    });
}

function shouldAutoRefresh() {
    const timeSinceLastUpdate = Date.now() - AITrendsApp.state.lastUpdateTime;
    return timeSinceLastUpdate > AITrendsApp.config.refreshInterval;
}

function performAutoRefresh() {
    console.log('Performing auto-refresh...');
    
    // Only refresh if on the main dashboard
    if (window.location.pathname === '/') {
        // Show subtle loading indicator
        showSubtleRefreshIndicator();
        
        // Reload the page
        setTimeout(() => {
            location.reload();
        }, 1000);
    }
    
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
        console.error('HTMX request failed:', evt.detail);
        hideLoadingOverlay();
        showError('Failed to load content. Please try again.');
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
    try {
        const toast = document.getElementById('errorToast');
        const toastBody = document.getElementById('errorToastBody');
        
        if (toast && toastBody && typeof bootstrap !== 'undefined') {
            toastBody.textContent = message;
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        } else {
            console.error('Error:', message);
            // Fallback to alert if Bootstrap isn't available
            alert('Error: ' + message);
        }
    } catch (error) {
        console.error('Error showing error toast:', error);
        console.error('Error:', message);
        alert('Error: ' + message);
    }
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
