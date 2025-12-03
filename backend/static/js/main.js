// HRMS Custom JavaScript - Enhanced User Experience

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize all interactive components
    initializeComponents();
    
    // Initialize page-specific enhancements
    initializePageEnhancements();
    
    // Setup global event listeners
    setupGlobalListeners();
    
});

function initializeComponents() {
    // Initialize tooltips (if using them)
    initializeTooltips();
    
    // Initialize modals
    initializeModals();
    
    // Initialize form validations
    initializeFormValidation();
    
    // Initialize data tables
    initializeDataTables();
}

function initializePageEnhancements() {
    // Add loading states to buttons
    enhanceButtons();
    
    // Add smooth transitions to cards
    enhanceCards();
    
    // Initialize search functionality
    enhanceSearchFunctionality();
    
    // Add keyboard shortcuts
    initializeKeyboardShortcuts();
}

function setupGlobalListeners() {
    // Handle ajax form submissions
    setupAjaxForms();
    
    // Setup notification system
    setupNotifications();
    
    // Setup auto-save functionality
    setupAutoSave();
}

// Button enhancements
function enhanceButtons() {
    const buttons = document.querySelectorAll('button[type="submit"], .btn-primary, .btn-success');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!this.disabled) {
                // Add loading state
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Loading...';
                this.disabled = true;
                
                // Reset after 3 seconds if no form submission
                setTimeout(() => {
                    if (this.disabled) {
                        this.innerHTML = originalText;
                        this.disabled = false;
                    }
                }, 3000);
            }
        });
    });
}

// Card hover enhancements
function enhanceCards() {
    const cards = document.querySelectorAll('.card, [class*="bg-white"], [class*="bg-gray"]');
    
    cards.forEach(card => {
        if (!card.classList.contains('no-hover')) {
            card.classList.add('card-hover');
        }
    });
}

// Search functionality enhancement
function enhanceSearchFunctionality() {
    const searchInputs = document.querySelectorAll('input[type="search"], .search-input');
    
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            // Add loading indicator
            const searchContainer = this.closest('.relative') || this.parentElement;
            let loader = searchContainer.querySelector('.search-loader');
            
            if (!loader) {
                loader = document.createElement('div');
                loader.className = 'search-loader absolute right-3 top-1/2 transform -translate-y-1/2';
                loader.innerHTML = '<div class="spinner w-4 h-4"></div>';
                searchContainer.appendChild(loader);
            }
            
            loader.style.display = 'block';
            
            // Debounce search
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
                loader.style.display = 'none';
            }, 300);
        });
    });
}

function performSearch(query) {
    // This would typically make an AJAX call to search endpoints
    console.log('Searching for:', query);
    
    // Example: Filter visible elements
    const searchableItems = document.querySelectorAll('[data-searchable]');
    
    searchableItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        const match = text.includes(query.toLowerCase());
        
        if (query === '' || match) {
            item.style.display = '';
            item.classList.remove('hidden');
        } else {
            item.style.display = 'none';
            item.classList.add('hidden');
        }
    });
}

// Keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for global search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // ESC to close modals/dropdowns
        if (e.key === 'Escape') {
            closeAllDropdowns();
            closeAllModals();
        }
        
        // Arrow key navigation for dropdown menus
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            handleDropdownNavigation(e);
        }
    });
}

function closeAllDropdowns() {
    const dropdowns = document.querySelectorAll('.group-hover\\:opacity-100');
    dropdowns.forEach(dropdown => {
        dropdown.classList.add('opacity-0', 'invisible');
        dropdown.classList.remove('opacity-100', 'visible');
    });
}

function closeAllModals() {
    const modals = document.querySelectorAll('.modal, [data-modal]');
    modals.forEach(modal => {
        modal.classList.add('hidden');
    });
}

// Tooltip initialization
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const text = e.target.dataset.tooltip;
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip absolute z-50 bg-gray-800 text-white text-sm rounded px-2 py-1 pointer-events-none';
    tooltip.textContent = text;
    tooltip.id = 'active-tooltip';
    
    document.body.appendChild(tooltip);
    
    // Position tooltip
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('active-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Modal functionality
function initializeModals() {
    const modalTriggers = document.querySelectorAll('[data-modal-target]');
    const modalClosers = document.querySelectorAll('[data-modal-close]');
    
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function() {
            const modalId = this.dataset.modalTarget;
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('hidden');
                modal.classList.add('flex');
            }
        });
    });
    
    modalClosers.forEach(closer => {
        closer.addEventListener('click', function() {
            const modal = this.closest('.modal') || document.querySelector('.modal:not(.hidden)');
            if (modal) {
                modal.classList.add('hidden');
                modal.classList.remove('flex');
            }
        });
    });
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    const isRequired = field.hasAttribute('required');
    const fieldType = field.type;
    
    // Remove existing error messages
    const existingError = field.parentElement.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    let isValid = true;
    let errorMessage = '';
    
    // Required field validation
    if (isRequired && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Email validation
    if (fieldType === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    // Phone validation
    if (field.name === 'phone' && value) {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        if (!phoneRegex.test(value.replace(/[\s\-\(\)]/g, ''))) {
            isValid = false;
            errorMessage = 'Please enter a valid phone number';
        }
    }
    
    // Update field styling and show error
    if (!isValid) {
        field.classList.add('border-red-500', 'focus:border-red-500');
        field.classList.remove('border-gray-300');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-red-500 text-sm mt-1';
        errorDiv.textContent = errorMessage;
        field.parentElement.appendChild(errorDiv);
    } else {
        field.classList.remove('border-red-500', 'focus:border-red-500');
        field.classList.add('border-gray-300');
    }
    
    return isValid;
}

// Data table enhancements
function initializeDataTables() {
    const tables = document.querySelectorAll('.data-table');
    
    tables.forEach(table => {
        // Add sorting functionality
        const headers = table.querySelectorAll('th[data-sortable]');
        headers.forEach(header => {
            header.classList.add('cursor-pointer', 'hover:bg-gray-100', 'select-none');
            header.innerHTML += ' <i class="fas fa-sort text-gray-400 ml-1"></i>';
            
            header.addEventListener('click', function() {
                sortTable(table, this);
            });
        });
    });
}

function sortTable(table, header) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentElement.children).indexOf(header);
    const isAscending = !header.classList.contains('sort-asc');
    
    // Reset all headers
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        const icon = th.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-sort text-gray-400 ml-1';
        }
    });
    
    // Update current header
    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
    const icon = header.querySelector('i');
    if (icon) {
        icon.className = `fas fa-sort-${isAscending ? 'up' : 'down'} text-blue-600 ml-1`;
    }
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        // Try to parse as numbers
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        
        // String comparison
        return isAscending ? 
            aValue.localeCompare(bValue) : 
            bValue.localeCompare(aValue);
    });
    
    // Reorder rows in DOM
    rows.forEach(row => tbody.appendChild(row));
}

// AJAX form handling
function setupAjaxForms() {
    const ajaxForms = document.querySelectorAll('form[data-ajax]');
    
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const url = this.action || window.location.href;
            const method = this.method || 'POST';
            
            // Show loading state
            const submitButton = this.querySelector('button[type="submit"]');
            const originalText = submitButton?.innerHTML;
            if (submitButton) {
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Submitting...';
                submitButton.disabled = true;
            }
            
            fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Success: ' + data.message, 'success');
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    }
                } else {
                    showNotification('Error: ' + (data.message || 'Something went wrong'), 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Network error occurred', 'error');
            })
            .finally(() => {
                // Reset button state
                if (submitButton && originalText) {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }
            });
        });
    });
}

// Notification system
function setupNotifications() {
    // This would integrate with Django messages framework
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 translate-x-full`;
    
    const bgColor = {
        'success': 'bg-green-500',
        'error': 'bg-red-500', 
        'warning': 'bg-yellow-500',
        'info': 'bg-blue-500'
    }[type] || 'bg-blue-500';
    
    notification.classList.add(bgColor, 'text-white');
    notification.innerHTML = `
        <div class="flex items-center justify-between">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.remove('translate-x-full'), 100);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Auto-save functionality
function setupAutoSave() {
    const autoSaveForms = document.querySelectorAll('form[data-autosave]');
    
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                // Implement auto-save logic here
                console.log('Auto-saving form data...');
            });
        });
    });
}

// Export functions for global use
window.HRMS = {
    showNotification,
    validateForm,
    validateField,
    sortTable
};