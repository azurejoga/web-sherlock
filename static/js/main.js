/**
 * Web Sherlock - Main JavaScript functionality
 */

// Global variables
let searchInProgress = false;

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize file upload handling
    initializeFileUpload();
    
    // Initialize accessibility features
    initializeAccessibility();
    
    console.log('Web Sherlock application initialized');
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleFormSubmit);
        
        // Real-time validation
        const usernamesField = document.getElementById('usernames');
        const jsonFileField = document.getElementById('json_file');
        
        if (usernamesField) {
            usernamesField.addEventListener('input', validateForm);
        }
        
        if (jsonFileField) {
            jsonFileField.addEventListener('change', validateForm);
        }
    }
}

/**
 * Handle form submission
 */
function handleFormSubmit(event) {
    if (searchInProgress) {
        event.preventDefault();
        return false;
    }
    
    const usernames = document.getElementById('usernames')?.value.trim() || '';
    const jsonFile = document.getElementById('json_file')?.files[0];
    
    // Validate inputs
    if (!usernames && !jsonFile) {
        event.preventDefault();
        showAlert('error', getErrorMessage('no_usernames'));
        return false;
    }
    
    // Validate JSON file if provided
    if (jsonFile && !validateJsonFile(jsonFile)) {
        event.preventDefault();
        return false;
    }
    
    // Show loading state
    setSearchInProgress(true);
    
    return true;
}

/**
 * Validate form inputs
 */
function validateForm() {
    const usernames = document.getElementById('usernames')?.value.trim() || '';
    const jsonFile = document.getElementById('json_file')?.files[0];
    const submitBtn = document.getElementById('submitBtn');
    
    const isValid = usernames || jsonFile;
    
    if (submitBtn) {
        submitBtn.disabled = !isValid || searchInProgress;
    }
    
    return isValid;
}

/**
 * Validate JSON file
 */
function validateJsonFile(file) {
    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        showAlert('error', 'File size too large. Maximum 5MB allowed.');
        return false;
    }
    
    // Check file type
    if (!file.type.includes('json') && !file.name.endsWith('.json')) {
        showAlert('error', 'Please upload a valid JSON file.');
        return false;
    }
    
    return true;
}

/**
 * Initialize file upload handling
 */
function initializeFileUpload() {
    const fileInput = document.getElementById('json_file');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileUpload);
    }
}

/**
 * Handle file upload
 */
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!validateJsonFile(file)) {
        event.target.value = '';
        return;
    }
    
    // Auto-check "local" option when JSON file is uploaded
    const localCheckbox = document.getElementById('local');
    if (localCheckbox) {
        localCheckbox.checked = true;
    }
    
    // Show file info
    const fileInfo = document.createElement('div');
    fileInfo.className = 'mt-2 small text-muted';
    fileInfo.innerHTML = `
        <i class="fas fa-file-check me-1"></i>
        Selected: ${file.name} (${formatFileSize(file.size)})
    `;
    
    // Remove existing file info
    const existingInfo = event.target.parentNode.querySelector('.file-info');
    if (existingInfo) {
        existingInfo.remove();
    }
    
    fileInfo.className += ' file-info';
    event.target.parentNode.appendChild(fileInfo);
    
    validateForm();
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Set search in progress state
 */
function setSearchInProgress(inProgress) {
    searchInProgress = inProgress;
    const submitBtn = document.getElementById('submitBtn');
    
    if (submitBtn) {
        if (inProgress) {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
            submitBtn.disabled = true;
            submitBtn.classList.add('btn-secondary');
            submitBtn.classList.remove('btn-primary');
        } else {
            submitBtn.innerHTML = '<i class="fas fa-search me-2"></i>Start Search';
            submitBtn.disabled = false;
            submitBtn.classList.add('btn-primary');
            submitBtn.classList.remove('btn-secondary');
        }
    }
}

/**
 * Show alert message
 */
function showAlert(type, message, container = null) {
    const alertClass = type === 'error' ? 'alert-danger' : 'alert-info';
    const iconClass = type === 'error' ? 'fas fa-exclamation-triangle' : 'fas fa-info-circle';
    
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <i class="${iconClass} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    const targetContainer = container || document.querySelector('.container > .row > .col-lg-8');
    if (targetContainer) {
        targetContainer.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = targetContainer.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
}

/**
 * Get error message based on key
 */
function getErrorMessage(key) {
    const messages = {
        'no_usernames': 'Please enter at least one username or upload a JSON file.',
        'invalid_json': 'Invalid JSON file format.',
        'file_too_large': 'File size too large. Maximum 5MB allowed.',
        'network_error': 'Network error. Please check your connection and try again.',
        'server_error': 'Server error. Please try again later.'
    };
    
    return messages[key] || 'An unexpected error occurred.';
}

/**
 * Initialize accessibility features
 */
function initializeAccessibility() {
    // Add skip link
    addSkipLink();
    
    // Enhance keyboard navigation
    enhanceKeyboardNavigation();
    
    // Add ARIA labels where needed
    addAriaLabels();
    
    // Handle focus management
    manageFocus();
}

/**
 * Add skip navigation link
 */
function addSkipLink() {
    const skipLink = document.createElement('a');
    skipLink.href = '#main';
    skipLink.className = 'sr-only sr-only-focusable btn btn-primary';
    skipLink.textContent = 'Skip to main content';
    skipLink.style.position = 'absolute';
    skipLink.style.top = '10px';
    skipLink.style.left = '10px';
    skipLink.style.zIndex = '9999';
    
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add main landmark
    const mainContent = document.querySelector('main');
    if (mainContent && !mainContent.id) {
        mainContent.id = 'main';
    }
}

/**
 * Enhance keyboard navigation
 */
function enhanceKeyboardNavigation() {
    // Handle Enter key on custom elements
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            const target = event.target;
            
            // Handle custom buttons
            if (target.getAttribute('role') === 'button' && !target.disabled) {
                event.preventDefault();
                target.click();
            }
        }
        
        // Handle Escape key
        if (event.key === 'Escape') {
            // Close any open modals or dropdowns
            const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
            openDropdowns.forEach(dropdown => {
                const toggle = dropdown.previousElementSibling;
                if (toggle) {
                    bootstrap.Dropdown.getInstance(toggle)?.hide();
                }
            });
        }
    });
}

/**
 * Add ARIA labels where needed
 */
function addAriaLabels() {
    // Add labels to form controls without labels
    const formControls = document.querySelectorAll('input, select, textarea');
    formControls.forEach(control => {
        if (!control.getAttribute('aria-label') && !control.getAttribute('aria-labelledby')) {
            const label = document.querySelector(`label[for="${control.id}"]`);
            if (label) {
                control.setAttribute('aria-labelledby', label.id || `label-${control.id}`);
                if (!label.id) {
                    label.id = `label-${control.id}`;
                }
            }
        }
    });
    
    // Add labels to buttons without text
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        if (!button.textContent.trim() && !button.getAttribute('aria-label')) {
            const icon = button.querySelector('i');
            if (icon) {
                const iconClass = icon.className;
                if (iconClass.includes('fa-search')) {
                    button.setAttribute('aria-label', 'Search');
                } else if (iconClass.includes('fa-download')) {
                    button.setAttribute('aria-label', 'Download');
                }
            }
        }
    });
}

/**
 * Manage focus
 */
function manageFocus() {
    // Store the last focused element before page transitions
    let lastFocusedElement = null;
    
    document.addEventListener('focusin', function(event) {
        lastFocusedElement = event.target;
    });
    
    // Focus management for dynamic content
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Focus first interactive element in new content
                        const firstInteractive = node.querySelector('button, input, select, textarea, a[href]');
                        if (firstInteractive && !document.activeElement.closest('.modal')) {
                            // Only focus if not in a modal
                            setTimeout(() => firstInteractive.focus(), 100);
                        }
                    }
                });
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

/**
 * Utility functions
 */

/**
 * Debounce function
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

/**
 * Throttle function
 */
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
    };
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            textArea.remove();
            return Promise.resolve();
        } catch (error) {
            textArea.remove();
            return Promise.reject(error);
        }
    }
}

/**
 * Format timestamp
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

/**
 * Validate URL
 */
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

/**
 * Export functionality (used in results page)
 */
window.exportResults = function(format) {
    const searchId = window.searchId;
    if (!searchId) {
        showAlert('error', 'No search results to export.');
        return;
    }
    
    // Show loading state
    const button = event.target.closest('button');
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Exporting...';
    button.disabled = true;
    
    // Create download link
    const link = document.createElement('a');
    link.href = `/export/${searchId}/${format}`;
    link.download = `sherlock_results_${searchId}.${format}`;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Restore button state
    setTimeout(() => {
        button.innerHTML = originalContent;
        button.disabled = false;
    }, 1000);
};

/**
 * Toggle found filter (used in results page)
 */
window.toggleFound = function() {
    // This function is implemented in the results.html template
    // as it needs access to template variables
};

// Make functions available globally for template usage
window.WebSherlock = {
    showAlert,
    copyToClipboard,
    formatTimestamp,
    isValidUrl,
    debounce,
    throttle
};
